"""
Storage abstraction layer for document file storage.

Supports multiple backends:
- Local filesystem storage
- AWS S3 storage

Provides unified interface for upload, download, delete operations
and presigned URL generation for secure access.
"""

from __future__ import annotations

import io
import os
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Protocol
from uuid import UUID

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    async def upload(self, file_bytes: bytes, storage_path: str) -> str:
        """
        Upload file to storage backend.

        Args:
            file_bytes: File content as bytes
            storage_path: Target path (e.g., "documents/uuid/filename.pdf")

        Returns:
            Storage path or URL for the uploaded file
        """
        pass

    @abstractmethod
    async def download(self, storage_path: str) -> bytes:
        """
        Download file from storage backend.

        Args:
            storage_path: Path to retrieve

        Returns:
            File content as bytes
        """
        pass

    @abstractmethod
    async def delete(self, storage_path: str) -> bool:
        """
        Delete file from storage backend.

        Args:
            storage_path: Path to delete

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def get_presigned_url(self, storage_path: str, expires_in_minutes: int = 15) -> str:
        """
        Generate a presigned URL for secure temporary access.

        Args:
            storage_path: Path to generate URL for
            expires_in_minutes: URL validity duration

        Returns:
            Presigned URL valid for specified duration
        """
        pass


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage backend."""

    def __init__(self):
        """Initialize local storage backend."""
        self.base_path = settings.LOCAL_STORAGE_PATH
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info_context("Local storage initialized", base_path=str(self.base_path))

    async def upload(self, file_bytes: bytes, storage_path: str) -> str:
        """Upload file to local filesystem."""
        full_path = self.base_path / storage_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            full_path.write_bytes(file_bytes)
            logger.info_context(
                "File uploaded to local storage",
                storage_path=storage_path,
                file_size=len(file_bytes),
            )
            return str(full_path)
        except Exception as e:
            logger.error_context(
                "Failed to upload file to local storage",
                storage_path=storage_path,
                exc_info=True,
            )
            raise

    async def download(self, storage_path: str) -> bytes:
        """Download file from local filesystem."""
        full_path = self.base_path / storage_path

        try:
            file_bytes = full_path.read_bytes()
            logger.info_context(
                "File downloaded from local storage",
                storage_path=storage_path,
                file_size=len(file_bytes),
            )
            return file_bytes
        except FileNotFoundError:
            logger.warning_context("File not found in local storage", storage_path=storage_path)
            raise
        except Exception as e:
            logger.error_context(
                "Failed to download file from local storage",
                storage_path=storage_path,
                exc_info=True,
            )
            raise

    async def delete(self, storage_path: str) -> bool:
        """Delete file from local filesystem."""
        full_path = self.base_path / storage_path

        try:
            if full_path.exists():
                full_path.unlink()
                logger.info_context("File deleted from local storage", storage_path=storage_path)
                return True
            return False
        except Exception as e:
            logger.error_context(
                "Failed to delete file from local storage",
                storage_path=storage_path,
                exc_info=True,
            )
            raise

    async def get_presigned_url(self, storage_path: str, expires_in_minutes: int = 15) -> str:
        """
        Generate a presigned URL for local storage.

        For local storage, this returns a file:// URL with expiration info.
        In production with reverse proxy, configure /storage route to serve files.

        Returns file path that can be resolved by frontend.
        """
        full_path = self.base_path / storage_path

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {storage_path}")

        # For local development, return file path
        # In production, configure nginx to serve from /storage path
        logger.info_context(
            "Presigned URL generated for local storage",
            storage_path=storage_path,
            expires_in_minutes=expires_in_minutes,
        )

        return f"/storage/{storage_path}"


class S3StorageBackend(StorageBackend):
    """AWS S3 storage backend."""

    def __init__(self):
        """Initialize S3 storage backend."""
        try:
            import boto3
            from botocore.exceptions import NoCredentialsError

            self.boto3 = boto3
            self.NoCredentialsError = NoCredentialsError

            if not settings.S3_BUCKET_NAME:
                raise ValueError("S3_BUCKET_NAME not configured")

            # Configure S3 client
            client_kwargs = {
                "region_name": getattr(settings, "AWS_REGION", "us-east-1"),
            }

            if settings.S3_ENDPOINT_URL:
                client_kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL

            self.s3_client = boto3.client("s3", **client_kwargs)
            self.bucket_name = settings.S3_BUCKET_NAME

            logger.info_context(
                "S3 storage initialized",
                bucket=self.bucket_name,
                endpoint_url=settings.S3_ENDPOINT_URL,
            )
        except ImportError:
            logger.error("boto3 not installed. Install with: pip install boto3")
            raise
        except Exception as e:
            logger.error_context("Failed to initialize S3 storage", exc_info=True)
            raise

    async def upload(self, file_bytes: bytes, storage_path: str) -> str:
        """Upload file to S3."""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=storage_path,
                Body=file_bytes,
                ContentType="application/pdf",
            )

            logger.info_context(
                "File uploaded to S3",
                bucket=self.bucket_name,
                key=storage_path,
                file_size=len(file_bytes),
            )

            # Return S3 URI
            return f"s3://{self.bucket_name}/{storage_path}"

        except self.NoCredentialsError:
            logger.error("AWS credentials not found")
            raise
        except Exception as e:
            logger.error_context(
                "Failed to upload file to S3",
                bucket=self.bucket_name,
                key=storage_path,
                exc_info=True,
            )
            raise

    async def download(self, storage_path: str) -> bytes:
        """Download file from S3."""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=storage_path)
            file_bytes = response["Body"].read()

            logger.info_context(
                "File downloaded from S3",
                bucket=self.bucket_name,
                key=storage_path,
                file_size=len(file_bytes),
            )

            return file_bytes

        except self.s3_client.exceptions.NoSuchKey:
            logger.warning_context(
                "File not found in S3",
                bucket=self.bucket_name,
                key=storage_path,
            )
            raise FileNotFoundError(f"File not found in S3: {storage_path}")
        except Exception as e:
            logger.error_context(
                "Failed to download file from S3",
                bucket=self.bucket_name,
                key=storage_path,
                exc_info=True,
            )
            raise

    async def delete(self, storage_path: str) -> bool:
        """Delete file from S3."""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=storage_path)

            logger.info_context(
                "File deleted from S3",
                bucket=self.bucket_name,
                key=storage_path,
            )

            return True
        except Exception as e:
            logger.error_context(
                "Failed to delete file from S3",
                bucket=self.bucket_name,
                key=storage_path,
                exc_info=True,
            )
            raise

    async def get_presigned_url(self, storage_path: str, expires_in_minutes: int = 15) -> str:
        """Generate a presigned S3 URL."""
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": storage_path},
                ExpiresIn=expires_in_minutes * 60,
            )

            logger.info_context(
                "Presigned S3 URL generated",
                bucket=self.bucket_name,
                key=storage_path,
                expires_in_minutes=expires_in_minutes,
            )

            return url
        except Exception as e:
            logger.error_context(
                "Failed to generate presigned S3 URL",
                bucket=self.bucket_name,
                key=storage_path,
                exc_info=True,
            )
            raise


def get_storage_backend() -> StorageBackend:
    """Get configured storage backend."""
    if settings.STORAGE_BACKEND == "s3":
        return S3StorageBackend()
    elif settings.STORAGE_BACKEND == "local":
        return LocalStorageBackend()
    else:
        raise ValueError(f"Unknown storage backend: {settings.STORAGE_BACKEND}")
