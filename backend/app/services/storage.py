import io
import boto3
from botocore.exceptions import ClientError

from ..config import settings

s3 = boto3.client(
    "s3",
    endpoint_url=settings.MINIO_ENDPOINT,
    aws_access_key_id=settings.MINIO_ACCESS_KEY,
    aws_secret_access_key=settings.MINIO_SECRET_KEY,
)


def ensure_bucket():
    try:
        s3.head_bucket(Bucket=settings.MINIO_BUCKET)
    except ClientError:
        s3.create_bucket(Bucket=settings.MINIO_BUCKET)


def upload_fileobj(fileobj: io.BytesIO, key: str) -> str:
    ensure_bucket()
    s3.upload_fileobj(fileobj, settings.MINIO_BUCKET, key)
    return key


def download_bytes(key: str) -> bytes:
    buf = io.BytesIO()
    s3.download_fileobj(settings.MINIO_BUCKET, key, buf)
    return buf.getvalue()


def delete_file(key: str) -> None:
    try:
        s3.delete_object(Bucket=settings.MINIO_BUCKET, Key=key)
    except ClientError as e:
        raise Exception(f"Failed to delete file from storage: {e}")
