import asyncio
from typing import Any

from app.core.config import Settings


class S3AudioStorage:
    def __init__(self, settings: Settings) -> None:
        import boto3

        self._settings = settings
        self._client: Any = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
        )

    async def ensure_ready(self) -> None:
        await asyncio.to_thread(self._ensure_bucket_sync)

    def _ensure_bucket_sync(self) -> None:
        buckets = self._client.list_buckets().get("Buckets", [])
        names = {bucket["Name"] for bucket in buckets}
        if self._settings.s3_bucket not in names:
            self._client.create_bucket(Bucket=self._settings.s3_bucket)

    async def upload(self, key: str, data: bytes, content_type: str) -> None:
        await asyncio.to_thread(
            self._client.put_object,
            Bucket=self._settings.s3_bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )

    async def download(self, key: str) -> tuple[bytes, str]:
        response = await asyncio.to_thread(
            self._client.get_object,
            Bucket=self._settings.s3_bucket,
            Key=key,
        )
        body = response["Body"].read()
        content_type = str(response.get("ContentType", "application/octet-stream"))
        return body, content_type
