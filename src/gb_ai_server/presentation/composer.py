"""Composition root — orchestrates the full bootstrap workflow."""

from __future__ import annotations

import os
import traceback
from argparse import Namespace
from pathlib import Path

from typing import TYPE_CHECKING

from gb_ai_server.domain import ModelEntry, PortAllocator, ContainerNamer
from gb_ai_server.infrastructure import (
    InfrastructureRegistry,
    VerifierFactory,
    ComposeServiceFactory,
    ModelServiceFactory,
    Environment,
    HuggingFaceModelDownloader,
    ClineModelRegistrar,
)
from gb_ai_server.infrastructure.paths import ModelPathResolver
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

COMPOSE_SERVICE_NAME = "llama"


def _estimate_model_size_gb(model: ModelEntry) -> float:
    """Estimate model size in GB from local GGUF file or HF API."""
    # Try local GGUF file first
    try:
        from pathlib import Path
        import os
        vol = os.path.expanduser(
            "~/.local/share/containers/storage/volumes/llama_models/_data"
        )
        candidate = Path(vol) / model.filename
        if candidate.exists():
            return candidate.stat().st_size / 1e9
    except Exception:
        pass

    # Try HF model resolver
    try:
        from gb_ai_server.infrastructure.persistence.hf_model_resolver import resolve_model
        repo_id = None
        for part in model.url.split("/"):
            if part.endswith("-GGUF") or part.endswith("-gguf"):
                idx = model.url.index(part)
                url_path = model.url[:idx + len(part)].replace("https://huggingface.co/", "")
                # Extract org/repo from URL
                parts = model.url.replace("https://huggingface.co/", "").split("/")
                repo_id = "/".join(parts[:2])
                break
        if repo_id:
            resolved = resolve_model(repo_id)
            if resolved:
                return resolved.size_gb
    except Exception:
        pass

    return 8.0  # sensible default for Q4_K_M quantized models


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
            self._ensure_cdi()
            resolver = ModelPathResolver(args.models_dirs)

            running_model = self._detect_running_model(prereqs.inspector, model)
            if running_model is not None:
                if running_model == model.filename:
                    _, _, port = self._get_service_info(model)
                    self._model_selection_presenter.model_already_running(model.display_name)
                    self._register_models(resolver, model)
                    self._service_presenter.report_success(display_name=model.display_name, port=port)
                    return 0
                self._model_selection_presenter.switching_model(
                    self._model_name_for_filename(all_models, running_model),
                    model.display_name,
                )
                self._stop_running_service(prereqs.compose_lifecycle, env)

            model_path = self._ensure_model_available(resolver, model, args)
            if model_path is None:
                return 1

            self._start_services(prereqs.compose_lifecycle, env, model)
            self._copy_models(prereqs.inspector, prereqs.operator, model, model_path, args)
            self._restart_services(prereqs.compose_lifecycle, env, model)
            self._verify_health(args, model)
            self._register_models(resolver, model)
            _, _, port = self._get_service_info(model)
            self._service_presenter.report_success(display_name=model.display_name, port=port)
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
        # Single model — always use the first (and only) configured model
        if not all_models:
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
        return (COMPOSE_SERVICE_NAME, ContainerNamer.name(), PortAllocator.port())

    def _set_model_env(self, model: ModelEntry) -> None:
        """Set LLAMA_MODEL, N_GPU_LAYERS, and CTX_SIZE environment variables.

        Both N_GPU_LAYERS and CTX_SIZE are calculated from HuggingFace model
        metadata and available VRAM — not hardcoded or pattern-matched.
        """
        from gb_ai_server.infrastructure.persistence.fetch_hf_ctx import (
            fetch_safe_ctx_size,
            fetch_model_metadata,
        )
        from gb_ai_server.infrastructure.persistence.hardware_prober import probe_hardware
        from gb_ai_server.domain.gpu_layer_calculator import GPULayerCalculator

        os.environ["LLAMA_MODEL"] = model.filename

        repo_id = (
            model.url.split("huggingface.co/")[-1].split("/resolve/")[0]
            if "huggingface.co" in model.url
            else model.display_name
        )

        # Context window from HF config.json + VRAM
        ctx = fetch_safe_ctx_size(repo_id)
        os.environ["CTX_SIZE"] = str(ctx)

        # GPU layers calculated from model architecture + VRAM
        hw = probe_hardware()
        metadata = fetch_model_metadata(repo_id)
        if metadata is not None and hw.vram_total_mb > 0:
            calc = GPULayerCalculator(metadata)
            result = calc.calculate_gpu_layers(hw.vram_total_mb)
            os.environ["N_GPU_LAYERS"] = str(result.gpu_layers)
            self._infra.logger.info(
                f"GPU layers: {result.gpu_layers}/{result.total_layers} "
                f"({result.per_layer_memory_mb:.0f}MB/layer, "
                f"VRAM={result.available_vram_mb:.0f}MB)"
            )
        else:
            # Fallback: offload all layers (llama.cpp default)
            os.environ["N_GPU_LAYERS"] = "999"

        # Write to .env so docker-compose picks it up (overrides existing values)
        env_path = Path(".env")
        if env_path.exists():
            lines = env_path.read_text().splitlines()
            new_lines = []
            written = {"LLAMA_MODEL", "N_GPU_LAYERS", "CTX_SIZE"}
            for line in lines:
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    new_lines.append(line)
                    continue
                key = stripped.split("=")[0].strip()
                if key in written and key in os.environ:
                    new_lines.append(f"{key}={os.environ[key]}")
                    written.discard(key)
                else:
                    new_lines.append(line)
            for key in written:
                if key in os.environ:
                    new_lines.append(f"{key}={os.environ[key]}")
            env_path.write_text("\n".join(new_lines) + "\n")

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
        # Allow VRAM to be fully released before starting new container
        import time
        time.sleep(3)

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

    def _ensure_cdi(self) -> None:
        """Ensure CDI is active for GPU passthrough before starting containers."""
        cdi = self._infra.cdi_service
        status = cdi.ensure()
        if not status.active:
            self._infra.logger.warn(
                "CDI not available — container may fall back to CPU"
            )

    def _ensure_model_available(
        self, resolver: ModelPathResolver, model: ModelEntry, args: Namespace
    ) -> Path | None:
        """Find model in any configured dir, or download to primary dir."""
        existing = resolver.resolve(model.filename)
        if existing is not None:
            self._infra.logger.info(
                f"{model.display_name} found at {existing}"
            )
            return existing

        if args.skip_download:
            self._prerequisite_presenter.skipping_download()
            self._model_selection_presenter.model_not_available(
                model.display_name, model.filename
            )
            return None

        # Check if model fits on hardware before downloading
        from gb_ai_server.infrastructure.persistence.hardware_prober import (
            probe_hardware,
            model_fits,
        )
        from gb_ai_server.infrastructure.persistence.fetch_hf_ctx import fetch_safe_ctx_size
        hw = probe_hardware()
        repo_id_for_ctx = (
            model.url.split("huggingface.co/")[-1].split("/resolve/")[0]
            if "huggingface.co" in model.url
            else model.display_name
        )
        ctx = fetch_safe_ctx_size(repo_id_for_ctx)

        # Estimate model size from GGUF metadata or HF
        model_size_gb = _estimate_model_size_gb(model)

        fits, reason = model_fits(hw, model_size_gb, ctx,
                                  gguf_path=str(resolver.primary() / model.filename))
        self._infra.logger.info(f"Hardware: {hw.gpu_name + ' ' if hw.gpu_name else ''}"
                                f"VRAM free={hw.vram_free_mb}MiB RAM={hw.ram_total_mb}MiB")
        self._infra.logger.info(f"Model: {model_size_gb:.1f}GB ctx={ctx} → {reason}")

        if not fits:
            self._infra.logger.error(
                f"Model {model.display_name} ({model_size_gb:.1f}GB, ctx={ctx}) "
                f"does not fit on this hardware. Try a smaller quantization."
            )
            return None

        hf_token = args.hf_token or os.getenv("HF_TOKEN")
        downloader = HuggingFaceModelDownloader(self._infra.logger, token=hf_token)
        service = self._models.model_downloader(downloader)
        response = service.execute(
            DownloadModelsRequest(
                entries=[(model.display_name, model.filename, model.url)],
                destination_dir=str(resolver.primary()),
                skip_existing=True,
                token=hf_token,
            )
        )
        if not any(response.results.values()):
            self._download_presenter.all_downloads_failed()
            return None

        resolved = resolver.resolve(model.filename)
        if resolved is None:
            self._infra.logger.error(
                f"Download completed but file not found at {resolver.primary() / model.filename}"
            )
            return None

        return resolved

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
        resolved_path: Path,
        args: Namespace,
    ) -> None:
        _, container_name, _ = self._get_service_info(model)
        service = self._models.model_copier(inspector, operator)
        response = service.execute(
            CopyModelsRequest(
                entries=[(model.display_name, model.filename, model.url)],
                source_dir=str(resolved_path.parent),
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

    def _register_models(self, resolver: ModelPathResolver, model: ModelEntry) -> None:
        model_path = resolver.resolve(model.filename)
        if model_path is None:
            self._model_selection_presenter.model_not_available(model.display_name, model.filename)
            return

        from gb_ai_server.application.services.register_custom_model_service import (
            register_custom_model,
        )

        repo_id = (
            model.url.split("huggingface.co/")[-1].split("/resolve/")[0]
            if "huggingface.co" in model.url
            else model.display_name
        )

        # Pass 0 — register_custom_model calls fetch_safe_ctx_size internally,
        # using HF config.json + live VRAM to compute the correct limit.
        results = register_custom_model(repo_id, 0)
        registered = [a for a, ok in results.items() if ok]
        if registered:
            self._registration_presenter.models_registered(registered)
        else:
            self._registration_presenter.registration_failed()

