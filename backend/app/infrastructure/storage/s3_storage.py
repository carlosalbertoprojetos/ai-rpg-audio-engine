import boto3
from botocore.client import BaseClient

from app.core.config import Settings


class S3AudioStorage:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: BaseClient = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
        )

    async def ensure_bucket(self) -> None:
        buckets = self._client.list_buckets().get("Buckets", [])
        names = {bucket["Name"] for bucket in buckets}
        if self._settings.s3_bucket not in names:
            self._client.create_bucket(Bucket=self._settings.s3_bucket)

