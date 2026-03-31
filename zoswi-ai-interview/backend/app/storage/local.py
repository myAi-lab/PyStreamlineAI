from pathlib import Path
import uuid

from app.storage.base import StorageBackend


class LocalStorageBackend(StorageBackend):
    def __init__(self, root_path: str) -> None:
        self.root = Path(root_path)
        self.root.mkdir(parents=True, exist_ok=True)

    async def save_file(self, *, file_name: str, content: bytes, content_type: str) -> str:
        safe_name = file_name.replace("..", "").replace("/", "_").replace("\\", "_")
        storage_key = f"{uuid.uuid4()}-{safe_name}"
        full_path = self.root / storage_key
        full_path.write_bytes(content)
        return storage_key

    async def read_file(self, storage_key: str) -> bytes:
        full_path = self.root / storage_key
        return full_path.read_bytes()

