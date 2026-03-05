class InMemoryAudioStorage:
    def __init__(self) -> None:
        self._items: dict[str, tuple[bytes, str]] = {}

    async def ensure_ready(self) -> None:
        return None

    async def upload(self, key: str, data: bytes, content_type: str) -> None:
        self._items[key] = (data, content_type)

    async def download(self, key: str) -> tuple[bytes, str]:
        value = self._items.get(key)
        if value is None:
            raise ValueError("audio object not found")
        return value

