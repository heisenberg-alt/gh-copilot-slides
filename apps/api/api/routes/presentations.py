"""
Presentation creation, retrieval, and export endpoints.
"""

import uuid
import asyncio
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from ..auth.entra import get_current_user, User
from ..storage.blob import BlobStorageService, get_blob_service

router = APIRouter()

# In-memory store for demo (replace with Redis/database in production)
_presentations: dict = {}
_progress: dict = {}


class CreatePresentationRequest(BaseModel):
    """Request body for creating a new presentation."""

    topic: str = Field(..., min_length=1, max_length=2000, description="Research topic")
    urls: list[str] = Field(default=[], description="Optional URLs for research")
    slide_count: int = Field(default=10, ge=3, le=30, description="Number of slides")
    purpose: str = Field(default="presentation", description="Purpose of presentation")
    mood: str = Field(default="", description="Mood/tone for styling")
    audience: str = Field(default="", description="Target audience")
    style_name: str = Field(default="", description="Style preset name")
    output_formats: list[str] = Field(
        default=["html"], description="Export formats: html, pptx, pdf"
    )
    template_blob_url: Optional[str] = Field(
        default=None, description="Azure Blob URL for uploaded PPTX template"
    )


class PresentationStatus(BaseModel):
    """Presentation status response."""

    session_id: str
    status: str  # "processing", "completed", "error"
    stage: Optional[str] = None
    progress: Optional[int] = None
    title: Optional[str] = None
    slide_count: Optional[int] = None
    output_urls: Optional[dict[str, str]] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ProgressEvent(BaseModel):
    """Progress update event for SSE."""

    stage: str
    message: str
    progress: int  # 0-100


@router.post("", response_model=PresentationStatus)
async def create_presentation(
    request: CreatePresentationRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    blob_service: BlobStorageService = Depends(get_blob_service),
):
    """
    Start creating a new presentation.

    Returns immediately with a session_id. Use the /stream endpoint
    to receive real-time progress updates.
    """
    session_id = str(uuid.uuid4())
    now = datetime.utcnow()

    # Initialize presentation record
    _presentations[session_id] = {
        "session_id": session_id,
        "user_id": user.id,
        "status": "processing",
        "stage": "initializing",
        "progress": 0,
        "title": None,
        "slide_count": None,
        "output_urls": None,
        "error": None,
        "created_at": now,
        "updated_at": now,
        "request": request.model_dump(),
    }

    # Initialize progress queue
    _progress[session_id] = asyncio.Queue()

    # Start background processing
    background_tasks.add_task(
        process_presentation,
        session_id=session_id,
        request=request,
        user_id=user.id,
        blob_service=blob_service,
    )

    return PresentationStatus(
        session_id=session_id,
        status="processing",
        stage="initializing",
        progress=0,
        created_at=now,
        updated_at=now,
    )


@router.get("/{session_id}", response_model=PresentationStatus)
async def get_presentation(
    session_id: str,
    user: User = Depends(get_current_user),
):
    """Get the current status of a presentation."""
    if session_id not in _presentations:
        raise HTTPException(status_code=404, detail="Presentation not found")

    pres = _presentations[session_id]

    # Check ownership
    if pres["user_id"] != user.id and "Admin" not in user.roles:
        raise HTTPException(status_code=403, detail="Access denied")

    return PresentationStatus(
        session_id=pres["session_id"],
        status=pres["status"],
        stage=pres.get("stage"),
        progress=pres.get("progress"),
        title=pres.get("title"),
        slide_count=pres.get("slide_count"),
        output_urls=pres.get("output_urls"),
        error=pres.get("error"),
        created_at=pres["created_at"],
        updated_at=pres["updated_at"],
    )


@router.get("/{session_id}/stream")
async def stream_progress(
    session_id: str,
    user: User = Depends(get_current_user),
):
    """
    Stream real-time progress updates via Server-Sent Events.

    Events include:
    - stage: Current processing stage
    - message: Human-readable status message
    - progress: Percentage complete (0-100)
    """
    if session_id not in _presentations:
        raise HTTPException(status_code=404, detail="Presentation not found")

    pres = _presentations[session_id]
    if pres["user_id"] != user.id and "Admin" not in user.roles:
        raise HTTPException(status_code=403, detail="Access denied")

    async def event_generator():
        """Generate SSE events from progress queue."""
        queue = _progress.get(session_id)
        if not queue:
            return

        while True:
            try:
                # Wait for next progress update
                event = await asyncio.wait_for(queue.get(), timeout=60.0)
                yield {
                    "event": "progress",
                    "data": event.model_dump_json(),
                }

                # Check if complete
                if event.progress >= 100 or event.stage in ("completed", "error"):
                    break
            except asyncio.TimeoutError:
                # Send keepalive
                yield {"event": "ping", "data": ""}

    return EventSourceResponse(event_generator())


@router.delete("/{session_id}")
async def delete_presentation(
    session_id: str,
    user: User = Depends(get_current_user),
):
    """Delete a presentation (admin only)."""
    if "Admin" not in user.roles:
        raise HTTPException(status_code=403, detail="Admin access required")

    if session_id not in _presentations:
        raise HTTPException(status_code=404, detail="Presentation not found")

    del _presentations[session_id]
    if session_id in _progress:
        del _progress[session_id]

    return {"message": "Presentation deleted"}


async def process_presentation(
    session_id: str,
    request: CreatePresentationRequest,
    user_id: str,
    blob_service: BlobStorageService,
):
    """
    Background task to process presentation creation.

    Uses the existing slide_mcp orchestrator pipeline.
    """
    queue = _progress.get(session_id)

    async def update_progress(stage: str, message: str, progress: int):
        """Helper to update progress."""
        _presentations[session_id]["stage"] = stage
        _presentations[session_id]["progress"] = progress
        _presentations[session_id]["updated_at"] = datetime.utcnow()
        if queue:
            await queue.put(ProgressEvent(stage=stage, message=message, progress=progress))

    try:
        # Stage 1: Research
        await update_progress("researching", "Gathering information on your topic...", 10)
        await asyncio.sleep(1)  # Simulate work

        # Import orchestrator
        from slide_mcp.agents.orchestrator import Orchestrator

        # Stage 2: Create orchestrator and run pipeline
        await update_progress("researching", "Analyzing sources and extracting insights...", 25)

        orchestrator = Orchestrator()
        result = await asyncio.to_thread(
            orchestrator.create_presentation,
            topic=request.topic,
            urls=request.urls,
            slide_count=request.slide_count,
            purpose=request.purpose,
            mood=request.mood,
            audience=request.audience,
            style_name=request.style_name,
        )

        await update_progress("curating", "Structuring slides and content...", 50)
        await asyncio.sleep(0.5)

        await update_progress("styling", "Applying visual design...", 70)
        await asyncio.sleep(0.5)

        # Stage 3: Export to requested formats
        await update_progress("exporting", "Generating output files...", 85)

        output_urls = {}
        for fmt in request.output_formats:
            if fmt == "html":
                from slide_mcp.exporters.html_exporter import export_html
                html_content = export_html(result)
                url = await blob_service.upload_output(
                    session_id, f"presentation.html", html_content.encode()
                )
                output_urls["html"] = url

            elif fmt == "pptx":
                from slide_mcp.exporters.pptx_exporter import export_pptx
                pptx_bytes = export_pptx(result)
                url = await blob_service.upload_output(
                    session_id, f"presentation.pptx", pptx_bytes
                )
                output_urls["pptx"] = url

            elif fmt == "pdf":
                from slide_mcp.exporters.pdf_exporter import export_pdf
                pdf_bytes = await asyncio.to_thread(export_pdf, result)
                url = await blob_service.upload_output(
                    session_id, f"presentation.pdf", pdf_bytes
                )
                output_urls["pdf"] = url

        # Complete
        _presentations[session_id]["status"] = "completed"
        _presentations[session_id]["title"] = result.get("title", "Untitled")
        _presentations[session_id]["slide_count"] = len(result.get("slides", []))
        _presentations[session_id]["output_urls"] = output_urls

        await update_progress("completed", "Presentation ready!", 100)

    except Exception as e:
        _presentations[session_id]["status"] = "error"
        _presentations[session_id]["error"] = str(e)
        await update_progress("error", f"Error: {str(e)}", 0)
