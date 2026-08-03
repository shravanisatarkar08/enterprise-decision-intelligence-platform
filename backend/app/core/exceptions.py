"""
core/exceptions.py
==================
Custom exception hierarchy for the EDIP application.

Architectural note:
  Defining domain-specific exceptions (rather than raising raw HTTPException
  everywhere) keeps the service layer free of FastAPI imports and makes it
  trivially testable with plain pytest – no ASGI test client required.

  The API layer maps each exception type to the correct HTTP status code
  via FastAPI exception handlers registered in main.py.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class EDIPException(Exception):
    """
    Root of the EDIP exception hierarchy.

    All custom exceptions inherit from here so callers can catch any
    application-level error with a single ``except EDIPException`` clause.
    """

    def __init__(self, detail: str, error_code: str) -> None:
        super().__init__(detail)
        self.detail = detail
        self.error_code = error_code


# ---------------------------------------------------------------------------
# Upload-domain exceptions
# ---------------------------------------------------------------------------

class EmptyFilenameError(EDIPException):
    """Raised when the uploaded file has no name."""

    def __init__(self) -> None:
        super().__init__(
            detail="No filename was provided. Please attach a valid file.",
            error_code="EMPTY_FILENAME",
        )


class UnsupportedFileTypeError(EDIPException):
    """Raised when the file extension is not in the allowed whitelist."""

    def __init__(self, extension: str, allowed: list[str]) -> None:
        super().__init__(
            detail=(
                f"File type '{extension}' is not supported. "
                f"Accepted types: {', '.join(allowed)}"
            ),
            error_code="UNSUPPORTED_FILE_TYPE",
        )


class FileTooLargeError(EDIPException):
    """Raised when the uploaded file exceeds the configured size limit."""

    def __init__(self, size_mb: float, limit_mb: float) -> None:
        super().__init__(
            detail=(
                f"File size {size_mb:.2f} MB exceeds the maximum allowed "
                f"size of {limit_mb:.2f} MB."
            ),
            error_code="FILE_TOO_LARGE",
        )


class FileParsingError(EDIPException):
    """Raised when pandas fails to parse the file contents."""

    def __init__(self, filename: str, original_error: str) -> None:
        super().__init__(
            detail=(
                f"Failed to parse '{filename}'. "
                f"Ensure the file is a valid CSV or Excel workbook. "
                f"Internal error: {original_error}"
            ),
            error_code="FILE_PARSING_ERROR",
        )


class FileStorageError(EDIPException):
    """Raised when the file cannot be persisted to disk."""

    def __init__(self, filename: str, original_error: str) -> None:
        super().__init__(
            detail=(
                f"Failed to save '{filename}' to storage. "
                f"Internal error: {original_error}"
            ),
            error_code="FILE_STORAGE_ERROR",
        )
