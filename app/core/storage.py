"""Storage service for file uploads (avatars, event media, etc.)"""

import os
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO

from app.core.settings import get_settings

settings = get_settings()


class StorageProvider(ABC):
    """Abstract base class for storage providers"""

    @abstractmethod
    async def upload(
        self, file: BinaryIO, filename: str, content_type: str, folder: str = ""
    ) -> str:
        """Upload file and return public URL"""
        pass

    @abstractmethod
    async def delete(self, file_url: str) -> None:
        """Delete file by URL"""
        pass

    @abstractmethod
    def get_public_url(self, file_path: str) -> str:
        """Get public URL for a file"""
        pass


class LocalStorage(StorageProvider):
    """Local filesystem storage provider"""

    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def upload(
        self, file: BinaryIO, filename: str, content_type: str, folder: str = ""
    ) -> str:
        """Save file to local filesystem"""
        file_ext = Path(filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_ext}"

        folder_path = self.upload_dir / folder
        folder_path.mkdir(parents=True, exist_ok=True)

        file_path = folder_path / unique_filename
        
        with open(file_path, "wb") as f:
            content = file.read()
            f.write(content)

        relative_path = f"{folder}/{unique_filename}" if folder else unique_filename
        return self.get_public_url(relative_path)

    async def delete(self, file_url: str) -> None:
        """Delete file from local filesystem"""
        try:
            file_path = file_url.replace(f"/{self.upload_dir.name}/", "")
            full_path = self.upload_dir / file_path
            if full_path.exists():
                full_path.unlink()
        except Exception:
            pass

    def get_public_url(self, file_path: str) -> str:
        """Get public URL for local file"""
        return f"/{self.upload_dir.name}/{file_path}"


class S3Storage(StorageProvider):
    """AWS S3 storage provider"""

    def __init__(
        self,
        bucket: str,
        access_key: str,
        secret_key: str,
        region: str = "us-east-1",
    ):
        try:
            import boto3
        except ImportError:
            raise ImportError(
                "boto3 is required for S3 storage. Install with: pip install boto3"
            )

        self.bucket = bucket
        self.region = region
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )

    async def upload(
        self, file: BinaryIO, filename: str, content_type: str, folder: str = ""
    ) -> str:
        """Upload file to S3"""
        file_ext = Path(filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        
        s3_key = f"{folder}/{unique_filename}" if folder else unique_filename

        content = file.read()
        
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=s3_key,
            Body=content,
            ContentType=content_type,
            ACL="public-read",
        )

        return self.get_public_url(s3_key)

    async def delete(self, file_url: str) -> None:
        """Delete file from S3"""
        try:
            s3_key = file_url.split(f"{self.bucket}.s3.amazonaws.com/")[-1]
            self.s3_client.delete_object(Bucket=self.bucket, Key=s3_key)
        except Exception:
            pass

    def get_public_url(self, file_path: str) -> str:
        """Get public URL for S3 file"""
        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{file_path}"


def get_storage_provider() -> StorageProvider:
    """Factory function to get configured storage provider"""
    provider = settings.STORAGE_PROVIDER.lower()

    if provider == "s3":
        if not all([settings.AWS_S3_BUCKET, settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY]):
            raise ValueError(
                "S3 storage requires AWS_S3_BUCKET, AWS_ACCESS_KEY_ID, and AWS_SECRET_ACCESS_KEY"
            )
        return S3Storage(
            bucket=settings.AWS_S3_BUCKET,
            access_key=settings.AWS_ACCESS_KEY_ID,
            secret_key=settings.AWS_SECRET_ACCESS_KEY,
            region=settings.AWS_REGION,
        )
    else:
        return LocalStorage(upload_dir=settings.UPLOAD_DIR)
