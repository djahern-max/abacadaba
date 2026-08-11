import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.config import settings


class StorageError(Exception):
    """Raised when the Spaces client cannot complete an operation."""


_client = boto3.client(
    "s3",
    endpoint_url=settings.spaces_endpoint,
    region_name=settings.spaces_region,
    aws_access_key_id=settings.spaces_key,
    aws_secret_access_key=settings.spaces_secret,
    config=Config(signature_version="s3v4"),
)


def generate_presigned_get(key: str, expires_in: int = 3600) -> str:
    try:
        return _client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.spaces_bucket, "Key": key},
            ExpiresIn=expires_in,
        )
    except (ClientError, BotoCoreError) as exc:
        raise StorageError(f"Could not generate a video URL: {exc}") from exc


def upload_fileobj(fileobj, key: str, content_type: str) -> None:
    try:
        _client.upload_fileobj(
            fileobj,
            settings.spaces_bucket,
            key,
            ExtraArgs={"ACL": "private", "ContentType": content_type},
        )
    except (ClientError, BotoCoreError) as exc:
        raise StorageError(f"Could not upload video: {exc}") from exc


def delete_object(key: str) -> None:
    try:
        _client.delete_object(Bucket=settings.spaces_bucket, Key=key)
    except (ClientError, BotoCoreError) as exc:
        raise StorageError(f"Could not delete object: {exc}") from exc


def object_exists(key: str) -> bool:
    try:
        _client.head_object(Bucket=settings.spaces_bucket, Key=key)
        return True
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")
        if error_code in ("404", "NoSuchKey", "NotFound"):
            return False
        raise StorageError(f"Could not check video existence: {exc}") from exc
    except BotoCoreError as exc:
        raise StorageError(f"Could not check video existence: {exc}") from exc
