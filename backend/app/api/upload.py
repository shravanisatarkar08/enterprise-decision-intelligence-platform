"""
api/upload.py
=============
FastAPI router for the dataset upload endpoint.

Architectural principle (Clean Architecture – API Layer):
  This module contains NO business logic.  Its sole responsibilities are:

    1. Declare the HTTP interface (method, path, status codes, tags).
    2. Forward the request to the service layer.
    3. Map domain exceptions to appropriate HTTP responses.
    4. Annotate everything so FastAPI auto-generates accurate Swagger docs.

If you find yourself writing an ``if``/``for`` here that isn't about HTTP
concerns, move that logic to ``services/upload_service.py``.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.exceptions import (
    EDIPException,
    EmptyFilenameError,
    FileParsingError,
    FileStorageError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from app.schemas.upload_schema import ErrorResponse, UploadResponse
from app.services.upload_service import UploadService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
# Using an APIRouter (not app directly) keeps routes modular and lets
# main.py include multiple routers without coupling.

router = APIRouter(
    prefix="/upload",
    tags=["Dataset Upload"],
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Invalid file (bad name, unsupported type, or corrupt content).",
            "model": ErrorResponse,
        },
        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE: {
            "description": "File exceeds the configured size limit.",
            "model": ErrorResponse,
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Unexpected server-side failure.",
            "model": ErrorResponse,
        },
    },
)

# Instantiate once per worker process (stateless, so this is safe).
_upload_service = UploadService()


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/",
    response_model=UploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload a dataset file",
    description=(
        "Accept a **CSV** or **XLSX** file, persist it to the uploads directory, "
        "and return an immediate statistical profile of the dataset.\n\n"
        "**Validations applied**:\n"
        "- Non-empty filename\n"
        "- Extension must be `.csv` or `.xlsx`\n"
        "- File size must not exceed the configured limit (default 50 MB)\n"
        "- Duplicate filenames are automatically renamed with a UUID suffix\n\n"
        "**Response** includes row/column counts, inferred data types, "
        "missing-value counts, duplicate-row count, and memory footprint."
    ),
    response_description="Dataset successfully uploaded and profiled.",
)
async def upload_dataset(
    file: UploadFile = File(
        ...,
        description="A CSV or XLSX dataset file. Maximum size is configurable (default 50 MB).",
    ),
) -> UploadResponse:
    """
    **POST /upload/**

    Upload a dataset file and receive an instant statistical profile.

    This endpoint is intentionally thin:

    - Read the file bytes from the ASGI upload stream.
    - Delegate all processing to :class:`~app.services.upload_service.UploadService`.
    - Catch domain exceptions and convert them to structured HTTP errors.

    Args:
        file: The multipart-encoded file sent by the client.

    Returns:
        :class:`~app.schemas.upload_schema.UploadResponse` with dataset statistics.

    Raises:
        HTTPException 400: Empty filename, unsupported extension, or corrupt file.
        HTTPException 413: File exceeds the configured maximum size.
        HTTPException 500: Unexpected internal error during storage or processing.
    """
    logger.info("Received upload request: filename='%s'", file.filename)

    # Read the full file into memory once.
    # For very large files a streaming approach (chunked reads) would be
    # preferable, but 50 MB is well within typical pod memory limits.
    file_bytes: bytes = await file.read()

    try:
        response = await _upload_service.process_upload(
            original_filename=file.filename or "",
            file_bytes=file_bytes,
        )
        return response

    # ------------------------------------------------------------------
    # Domain → HTTP exception mapping
    # ------------------------------------------------------------------
    except EmptyFilenameError as exc:
        _log_client_error(exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_error_detail(exc),
        ) from exc

    except UnsupportedFileTypeError as exc:
        _log_client_error(exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_error_detail(exc),
        ) from exc

    except FileTooLargeError as exc:
        _log_client_error(exc)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=_error_detail(exc),
        ) from exc

    except FileParsingError as exc:
        _log_client_error(exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_error_detail(exc),
        ) from exc

    except FileStorageError as exc:
        # Storage failures are server-side problems, not client errors.
        logger.error("Storage failure for '%s': %s", file.filename, exc.detail)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_error_detail(exc),
        ) from exc

    except EDIPException as exc:
        # Catch-all for any future domain exceptions not yet explicitly mapped.
        logger.exception("Unhandled domain exception for '%s'", file.filename)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_error_detail(exc),
        ) from exc


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _error_detail(exc: EDIPException) -> dict[str, str]:
    """
    Convert a domain exception into the structured dict that FastAPI
    serialises as the JSON ``detail`` field.

    Returning a dict (not just a string) allows clients to branch on
    ``error_code`` without parsing human-readable messages.
    """
    return {
        "message": exc.detail,
        "error_code": exc.error_code,
    }


def _log_client_error(exc: EDIPException) -> None:
    """Log at WARNING level (client errors are not server bugs)."""
    logger.warning("Client error [%s]: %s", exc.error_code, exc.detail)
