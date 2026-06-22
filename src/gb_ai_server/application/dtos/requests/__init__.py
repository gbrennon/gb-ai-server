"""Request DTOs for application inbound ports."""

from .download_models_request import DownloadModelsRequest
from .verify_prerequisites_request import VerifyPrerequisitesRequest
from .start_services_request import StartServicesRequest
from .stop_services_request import StopServicesRequest
from .restart_services_request import RestartServicesRequest
from .list_services_request import ListServicesRequest
from .show_logs_request import ShowLogsRequest
from .copy_models_request import CopyModelsRequest
from .verify_health_request import VerifyHealthRequest

__all__: list[str] = [
    "DownloadModelsRequest",
    "VerifyPrerequisitesRequest",
    "StartServicesRequest",
    "StopServicesRequest",
    "RestartServicesRequest",
    "ListServicesRequest",
    "ShowLogsRequest",
    "CopyModelsRequest",
    "VerifyHealthRequest",
]
