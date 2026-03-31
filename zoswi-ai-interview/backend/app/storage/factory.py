from app.core.config import Settings
from app.core.exceptions import PlatformException
from app.storage.base import StorageBackend
from app.storage.local import LocalStorageBackend


def build_storage_backend(settings: Settings) -> StorageBackend:
    if settings.storage_backend == "local":
        return LocalStorageBackend(root_path=settings.local_storage_path)

    raise PlatformException(
        code="storage_backend_not_ready",
        message="S3 backend is configured but runtime adapter is not enabled in this deployment.",
        status_code=500,
    )

