from typing import Protocol


class AudioStorage(Protocol):
    async def ensure_ready(self) -> None: ...

    async def upload(self, key: str, data: bytes, content_type: str) -> None: ...

    async def download(self, key: str) -> tuple[bytes, str]: ...

