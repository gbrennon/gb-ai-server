"""Composition root — orchestrates the full bootstrap workflow."""

from __future__ import annotations

import os
import traceback
from argparse import Namespace
from pathlib import Path

from typing import TYPE_CHECKING

from gb_ai_server.domain import ModelEntry
from gb_ai_server.infrastructure import (
    InfrastructureRegistry,
    VerifierFactory,
    ComposeServiceFactory,
    ModelServiceFactory,
    Environment,
    HuggingFaceModelDownloader,
    ClineModelRegistrar,
)
from gb_ai_server.application.dtos.responses import VerifyPrerequisitesResponse
from gb_ai_server.application.dtos.requests import (
    CopyModelsRequest,
    DownloadModelsRequest,
    RestartServicesRequest,
    StartServicesRequest,
    StopServicesRequest,
    VerifyHealthRequest,
    VerifyPrerequisitesRequest,
)
from gb_ai_server.presentation.presenter import (
    DownloadPresenter,
    ModelActionPresenter,
    ModelSelectionPresenter,
    PrerequisitePresenter,
    RegistrationPresenter,
    ServiceLifecyclePresenter,
)
from gb_ai_server.presentation.parser import load_models

if TYPE_CHECKING:
    from gb_ai_server.infrastructure import Container
    from gb_ai_server.application.ports.outbound import (
        ContainerInspector,
        ContainerOperator,
        ComposeLifecycle,
    )

CONTAINER_NAME = "llama-coder"
COMPOSE_SERVICE_NAME = "llama"
DEFAULT_PORT = 8081


class BootstrapCompositionRoot:
    """Wires services from the decomposed factories and orchestrate the bootstrap workflow."""

    def __init__(
        self,
        infrastructure: InfrastructureRegistry | Container,
        verifiers: VerifierFactory | None = None,
        compose: ComposeServiceFactory | None = None,
        models: ModelServiceFactory | None = None,
    ) -> None:
        if verifiers is None or compose is None or models is None:
            container = infrastructure
            self._infra = container
            self._verifiers = container
            self._compose = container
            self._models = container
            logger = container.logger
        else:
            self._infra = infrastructure
            self._verifiers = verifiers
            self._compose = compose
            self._models = models
            logger = infrastructure.logger
        self._prerequisite_presenter = PrerequisitePresenter(logger)
        self._download_presenter = DownloadPresenter(logger)
        self._service_presenter = ServiceLifecyclePresenter(logger)
        self._model_selection_presenter = ModelSelectionPresenter(logger)
        self._model_action_presenter = ModelActionPresenter(logger)
        self._registration_presenter = RegistrationPresenter(logger)

    def run(self, args: Namespace) -> int:
        if args.dry_run:
            self._infra.logger.info("Dry-run mode — no actions will be performed")
            return 0
        env = self._setup_environment(args)
        try:
            all_models = self._load_models_config(env)
            model = self._resolve_model(all_models, args)
            if model is None:
                return 1

            self._set_model_env(model)

            prereqs = self._verify_prerequisites(env)

            running_model = self._detect_running_model(prereqs.inspector, model)
            if running_model is not None:
                if running_model == model.filename:
                    _, _, port = self._get_service_info(model)
                    self._model_selection_presenter.model_already_running(model.display_name)
                    self._register_models(args, model)
                    self._service_presenter.report_success(port=port)
                    return 0
                self._model_selection_presenter.switching_model(
                    self._model_name_for_filename(all_models, running_model),
                    model.display_name,
                )
                self._stop_running_service(prereqs.compose_lifecycle, env)

            self._download_models(args, model)
            self._start_services(prereqs.compose_lifecycle, env, model)
            self._copy_models(prereqs.inspector, prereqs.operator, model, args)
            self._restart_services(prereqs.compose_lifecycle, env, model)
            self._verify_health(args, model)
            self._register_models(args, model)
            _, _, port = self._get_service_info(model)
            self._service_presenter.report_success(port=port)
            return 0
        except SystemExit:
            return 1
        except Exception as e:
            self._infra.logger.error(f"Bootstrap failed: {e}")
            if env.debug:
                traceback.print_exc()
            return 1

    def _setup_environment(self, args: Namespace) -> Environment:
        env = Environment.from_env()
        env.load_env_file(env.paths.env_file)
        if args.debug:
            env.debug = True
        if args.hf_token:
            os.environ["HF_TOKEN"] = args.hf_token
        return env

    def _load_models_config(self, env) -> list[ModelEntry]:
        models = load_models(env.paths.models_config_path)
        if not models:
            self._prerequisite_presenter.no_models_configured()
            raise SystemExit(1)
        return models

    def _resolve_model(
        self, all_models: list[ModelEntry], args: Namespace
    ) -> ModelEntry | None:
        if args.model:
            for m in all_models:
                if m.display_name == args.model:
                    return m
            self._model_selection_presenter.model_not_found(args.model)
            available = [(m.display_name, m.filename) for m in all_models]
            self._model_selection_presenter.list_available_models(available)
            return None

        return all_models[0]

    def _model_name_for_filename(
        self, models: list[ModelEntry], filename: str
    ) -> str:
        for m in models:
            if m.filename == filename:
                return m.display_name
        return filename

    def _get_service_info(self, model: ModelEntry) -> tuple[str, str, int]:
        return (COMPOSE_SERVICE_NAME, CONTAINER_NAME, DEFAULT_PORT)

    def _set_model_env(self, model: ModelEntry) -> None:
        os.environ["LLAMA_MODEL"] = model.filename
        os.environ["N_GPU_LAYERS"] = str(model.n_gpu_layers)
        os.environ["CTX_SIZE"] = str(model.ctx_size)

    def _detect_running_model(
        self, inspector: ContainerInspector | None, model: ModelEntry
    ) -> str | None:
        if inspector is None:
            return None
        _, container_name, _ = self._get_service_info(model)
        if not inspector.is_running(container_name):
            return None
        current_model = inspector.get_env(container_name, "LLAMA_MODEL")
        return current_model or None

    def _stop_running_service(
        self, compose_lifecycle: ComposeLifecycle | None, env: Environment
    ) -> None:
        service = self._compose.stop_services(compose_lifecycle)
        service.execute(
            StopServicesRequest(compose_file=str(env.paths.compose_file))
        )

    def _verify_prerequisites(self, env) -> VerifyPrerequisitesResponse:
        verifier = self._verifiers.prerequisite_verifier()
        result = verifier.execute(
            VerifyPrerequisitesRequest(str(env.paths.compose_file))
        )
        if not result.success:
            self._prerequisite_presenter.prerequisites_failed()
            raise SystemExit(1)
        if not result.compose_lifecycle or not result.container_runtime:
            self._prerequisite_presenter.detection_failed()
            raise SystemExit(1)
        return result

    def _download_models(self, args: Namespace, model: ModelEntry) -> None:
        if args.skip_download:
            self._prerequisite_presenter.skipping_download()
            return

        hf_token = args.hf_token or os.getenv("HF_TOKEN")
        downloader = HuggingFaceModelDownloader(self._infra.logger, token=hf_token)
        service = self._models.model_downloader(downloader)
        response = service.execute(
            DownloadModelsRequest(
                entries=[(model.display_name, model.filename, model.url)],
                destination_dir=str(args.models_dir),
                skip_existing=True,
                token=hf_token,
            )
        )
        if not any(response.results.values()):
            self._download_presenter.all_downloads_failed()
            raise SystemExit(1)

    def _start_services(self, compose_lifecycle: ComposeLifecycle | None, env, model: ModelEntry) -> None:
        service_name, _, _ = self._get_service_info(model)
        service = self._compose.start_services(compose_lifecycle)
        if not service.execute(
            StartServicesRequest(
                compose_file=str(env.paths.compose_file),
                services=(service_name,),
            )
        ).success:
            self._service_presenter.start_services_failed()
            raise SystemExit(1)

    def _copy_models(
        self,
        inspector: ContainerInspector | None,
        operator: ContainerOperator | None,
        model: ModelEntry,
        args: Namespace,
    ) -> None:
        _, container_name, _ = self._get_service_info(model)
        service = self._models.model_copier(inspector, operator)
        response = service.execute(
            CopyModelsRequest(
                entries=[(model.display_name, model.filename, model.url)],
                source_dir=str(args.models_dir),
                container_name=container_name,
                dest_dir="/models",
            )
        )
        if not any(response.results.values()):
            self._download_presenter.copy_models_failed()

    def _restart_services(self, compose_lifecycle: ComposeLifecycle | None, env, model: ModelEntry) -> None:
        service_name, _, _ = self._get_service_info(model)
        service = self._compose.restart_services(compose_lifecycle)
        if not service.execute(
            RestartServicesRequest(
                compose_file=str(env.paths.compose_file),
                services=(service_name,),
            )
        ).success:
            self._service_presenter.restart_failed()
            raise SystemExit(1)

    def _verify_health(self, args: Namespace, model: ModelEntry) -> None:
        if args.skip_health:
            return

        _, _, port = self._get_service_info(model)
        service = self._verifiers.health_verifier()
        if not service.execute(
            VerifyHealthRequest(
                ports=(port,),
                timeout_seconds=120,
                interval_seconds=5,
            )
        ).success:
            self._service_presenter.health_check_failed()
            raise SystemExit(1)

    def _register_models(self, args: Namespace, model: ModelEntry) -> None:
        model_path = Path(args.models_dir) / model.filename
        if not model_path.exists():
            self._model_selection_presenter.model_not_available(model.display_name, model.filename)
            return

        registrar = ClineModelRegistrar(self._infra.logger)
        service = self._models.model_registrar(registrar)

        _, container_name, port = self._get_service_info(model)
        model_tuple = (model.display_name, model.filename, port, container_name)

        from gb_ai_server.application.dtos.requests.register_models_request import RegisterModelsRequest
        request = RegisterModelsRequest(model=model_tuple)
        response = service.execute(request)
        if response.success:
            self._registration_presenter.models_registered([model.display_name])
        else:
            self._registration_presenter.registration_failed()

