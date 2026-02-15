"""
Azure Blob Storage client for file uploads and downloads.
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
import uuid

from azure.storage.blob import (
    BlobServiceClient,
    BlobSasPermissions,
    generate_blob_sas,
)

from ..config import settings


class BlobStorageService:
    """Azure Blob Storage service for handling file uploads and downloads."""

    def __init__(self, connection_string: Optional[str] = None):
        """Initialize the blob storage client."""
        conn_str = connection_string or settings.azure_storage_connection_string

        if conn_str:
            self._client = BlobServiceClient.from_connection_string(conn_str)
            self._uploads = self._client.get_container_client(
                settings.azure_storage_uploads_container
            )
            self._outputs = self._client.get_container_client(
                settings.azure_storage_outputs_container
            )
        else:
            # Mock mode for development
            self._client = None
            self._uploads = None
            self._outputs = None

    async def get_upload_url(
        self,
        user_id: str,
        filename: str,
        content_type: str,
    ) -> Tuple[str, str]:
        """
        Generate a SAS URL for uploading a file.

        Returns (upload_url, blob_url) tuple.
        """
        if not self._client:
            # Mock for development
            mock_url = f"https://mock-storage.blob.core.windows.net/uploads/{user_id}/{filename}"
            return mock_url, mock_url

        # Create unique blob name
        blob_name = f"{user_id}/{uuid.uuid4().hex[:8]}_{filename}"
        blob_client = self._uploads.get_blob_client(blob_name)

        # Generate SAS token for upload (valid for 1 hour)
        sas_token = generate_blob_sas(
            account_name=self._client.account_name,
            container_name=settings.azure_storage_uploads_container,
            blob_name=blob_name,
            permission=BlobSasPermissions(write=True, create=True),
            expiry=datetime.utcnow() + timedelta(hours=1),
        )

        upload_url = f"{blob_client.url}?{sas_token}"
        return upload_url, blob_client.url

    async def upload_output(
        self,
        session_id: str,
        filename: str,
        data: bytes,
    ) -> str:
        """
        Upload a generated output file and return a download URL.

        Returns a SAS URL valid for 24 hours.
        """
        if not self._client:
            # Mock for development
            return f"https://mock-storage.blob.core.windows.net/outputs/{session_id}/{filename}"

        blob_name = f"{session_id}/{filename}"
        blob_client = self._outputs.get_blob_client(blob_name)

        # Upload the file
        blob_client.upload_blob(data, overwrite=True)

        # Generate SAS token for download (valid for 24 hours)
        sas_token = generate_blob_sas(
            account_name=self._client.account_name,
            container_name=settings.azure_storage_outputs_container,
            blob_name=blob_name,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=24),
        )

        return f"{blob_client.url}?{sas_token}"

    async def delete_output(self, session_id: str):
        """Delete all outputs for a session."""
        if not self._client:
            return

        # List and delete all blobs with the session prefix
        prefix = f"{session_id}/"
        for blob in self._outputs.list_blobs(name_starts_with=prefix):
            self._outputs.delete_blob(blob.name)


# Dependency for FastAPI
_blob_service: Optional[BlobStorageService] = None


def get_blob_service() -> BlobStorageService:
    """Get the blob storage service instance."""
    global _blob_service
    if _blob_service is None:
        _blob_service = BlobStorageService()
    return _blob_service
