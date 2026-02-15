"""
Template upload endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth.entra import get_current_user, User
from ..storage.blob import BlobStorageService, get_blob_service

router = APIRouter()


class UploadUrlRequest(BaseModel):
    """Request for a presigned upload URL."""

    filename: str
    content_type: str = "application/vnd.openxmlformats-officedocument.presentationml.presentation"


class UploadUrlResponse(BaseModel):
    """Response containing upload URL and blob URL."""

    upload_url: str
    blob_url: str


@router.post("/upload-url", response_model=UploadUrlResponse)
async def get_upload_url(
    request: UploadUrlRequest,
    user: User = Depends(get_current_user),
    blob_service: BlobStorageService = Depends(get_blob_service),
):
    """
    Get a presigned URL for uploading a PPTX template.

    The client uploads directly to Azure Blob Storage using this URL,
    then provides the blob_url when creating a presentation.
    """
    # Validate file type
    if not request.filename.lower().endswith(".pptx"):
        raise HTTPException(
            status_code=400, detail="Only .pptx files are allowed"
        )

    # Generate upload URL
    upload_url, blob_url = await blob_service.get_upload_url(
        user_id=user.id,
        filename=request.filename,
        content_type=request.content_type,
    )

    return UploadUrlResponse(upload_url=upload_url, blob_url=blob_url)
