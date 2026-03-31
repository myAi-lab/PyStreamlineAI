from abc import ABC, abstractmethod


class StorageBackend(ABC):
    @abstractmethod
    async def save_file(self, *, file_name: str, content: bytes, content_type: str) -> str:
        raise NotImplementedError

    @abstractmethod
    async def read_file(self, storage_key: str) -> bytes:
        raise NotImplementedError

