"""Composition root — orchestrates the full bootstrap workflow."""

from __future__ import annotations

import os
import traceback
from argparse import Namespace

from gb_ai_server.domain import ModelEntry, PortAllocator
from gb_ai_server.infrastructure import Container, Environment, HuggingFaceModelDownloader, ClineModelRegistrar
from gb_ai_server.application.dtos.requests import (
    CopyModelsRequest,
    DownloadModelsRequest,
    RestartServicesRequest,
    StartServicesRequest,
    VerifyHealthRequest,
    VerifyPrerequisitesRequest,
)
from gb_ai_server.presentation.presenter import BootstrapPresenter
from gb_ai_server.application.services import PrerequisiteVerifierService
from gb_ai_server.presentation.parser import load_models


class BootstrapCompositionRoot:
    """Wires services from the DI container and orchestrates the bootstrap workflow."""

    def __init__(self, container: Container) -> None:
        self._di = container
        self._presenter = BootstrapPresenter(container.logger)

    def run(self, args: Namespace) -> int:
        if args.dry_run:
            self._di.logger.info("Dry-run mode — no actions will be performed")
            return 0
        env = self._setup_environment(args)
        try:
            models = self._load_models_config(env)
            verifier = self._verify_prerequisites(env)
            self._download_models(args, models)
            self._start_services(verifier, env)
            self._copy_models(verifier, models, args)
            self._restart_services(verifier, env)
            self._verify_health(args, models)
            self._register_models(models)
            self._presenter.report_success()
            return 0
        except SystemExit:
            return 1
        except Exception as e:
            self._di.logger.error(f"Bootstrap failed: {e}")
            if env.debug:
                traceback.print_exc()
            return 1

    def _setup_environment(self, args: Namespace) -> Environment:
        env = Environment.from_env()
        env.load_env_file(env.env_file)
        if args.debug:
            env.debug = True
        if args.hf_token:
            os.environ["HF_TOKEN"] = args.hf_token
        return env

    def _load_models_config(self, env) -> list[ModelEntry]:
        models = load_models(env.models_config_path)
        if not models:
            self._presenter.no_models_configured()
            raise SystemExit(1)
        return models

    def _verify_prerequisites(self, env):
        verifier = self._di.prerequisite_verifier()
        result = verifier.execute(
            VerifyPrerequisitesRequest(str(env.compose_file))
        )
        if not result.success:
            self._presenter.prerequisites_failed()
            raise SystemExit(1)
        if not verifier.compose_tool or not verifier.container_runtime:
            self._presenter.detection_failed()
            raise SystemExit(1)
        return verifier

    def _download_models(self, args: Namespace, models: list[ModelEntry]) -> None:
        if args.skip_download:
            self._presenter.skipping_download()
            return

        hf_token = args.hf_token or os.getenv("HF_TOKEN")
        downloader = HuggingFaceModelDownloader(self._di.logger, token=hf_token)
        service = self._di.model_downloader(downloader)
        response = service.execute(
            DownloadModelsRequest(
                entries=[(m.display_name, m.filename, m.url) for m in models],
                destination_dir=str(args.models_dir),
                skip_existing=True,
                token=hf_token,
            )
        )
        if not any(response.results.values()):
            self._presenter.all_downloads_failed()
            raise SystemExit(1)

    def _start_services(self, verifier: PrerequisiteVerifierService, env) -> None:
        service = self._di.start_services(verifier.compose_tool)
        if not service.execute(
            StartServicesRequest(
                compose_file=str(env.compose_file),
                services=("llama",),
            )
        ).success:
            self._presenter.start_services_failed()
            raise SystemExit(1)

    def _copy_models(
        self,
        verifier: PrerequisiteVerifierService,
        models: list[ModelEntry],
        args: Namespace,
    ) -> None:
        service = self._di.model_copier(verifier.container_runtime)
        response = service.execute(
            CopyModelsRequest(
                entries=[(m.display_name, m.filename, m.url) for m in models],
                source_dir=str(args.models_dir),
                container_name="llama-coder",
                dest_dir="/models",
            )
        )
        if not any(response.results.values()):
            self._presenter.copy_models_failed()

    def _restart_services(self, verifier: PrerequisiteVerifierService, env) -> None:
        service = self._di.restart_services(verifier.compose_tool)
        if not service.execute(
            RestartServicesRequest(
                compose_file=str(env.compose_file),
                services=("llama",),
            )
        ).success:
            self._presenter.restart_failed()
            raise SystemExit(1)

    def _verify_health(self, args: Namespace, models: list[ModelEntry]) -> None:
        if args.skip_health:
            return

        service = self._di.health_verifier()
        if not service.execute(
            VerifyHealthRequest(
                ports=tuple(PortAllocator.ports_for_models(len(models))),
                timeout_seconds=60,
                interval_seconds=5,
            )
        ).success:
            self._presenter.health_check_failed()
            raise SystemExit(1)

    def _register_models(self, models: list[ModelEntry]) -> None:
        registrar = ClineModelRegistrar(self._di.logger)
        service = self._di.model_registrar(registrar)

        # Map model index to container name based on docker-compose services
        # Primary service: llama -> llama-coder (port 8081)
        # Extra services: llama-qwen3 -> llama-qwen3 (port 8082), llama-devs -> llama-devs (port 8083)
        container_names = self._get_container_names(len(models))

        model_tuples = [
            (m.display_name, m.filename, port, container_name)
            for m, port, container_name in zip(
                models,
                PortAllocator.ports_for_models(len(models)),
                container_names,
            )
        ]

        from gb_ai_server.application.dtos.requests.register_models_request import RegisterModelsRequest
        request = RegisterModelsRequest(models=model_tuples)
        response = service.execute(request)
        if response.success:
            self._presenter.models_registered([m.display_name for m in models])
        else:
            self._presenter.registration_failed()

    def _get_container_names(self, model_count: int) -> list[str]:
        """Get container names for each model based on docker-compose service definitions."""
        # Default container names matching docker-compose.yml
        default_containers = ["llama-coder", "llama-qwen3", "llama-devs"]
        return default_containers[:model_count]
