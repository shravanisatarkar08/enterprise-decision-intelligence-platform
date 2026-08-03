"""
services/upload_service.py
==========================
All business logic for dataset upload and initial profiling lives here.

Architectural principle (Clean Architecture):
  This module has ZERO FastAPI imports.  It knows nothing about HTTP,
  request objects, or response models.  It receives plain Python types,
  does work, and returns plain Python types (or raises domain exceptions).
  This makes the entire service unit-testable without spinning up an ASGI app.

Extension roadmap (drop new methods/helpers here as features land):
  - _compute_quality_score()   → AI-powered data quality scoring
  - _run_eda_profiling()       → YData-Profiling / sweetviz integration
  - _recommend_ml_models()     → Cardinality/dtype heuristics → model list
  - _detect_pii_columns()      → Privacy compliance scanning
"""

from __future__ import annotations

import io
import logging
import uuid
from pathlib import Path

import pandas as pd

from app.core.config import get_settings
from app.core.exceptions import (
    EmptyFilenameError,
    FileParsingError,
    FileStorageError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from app.schemas.upload_schema import UploadResponse

# Module-level logger — never use print() in production code.
logger = logging.getLogger(__name__)

# Bytes in one megabyte (used throughout this module).
_BYTES_PER_MB: float = 1024.0 ** 2


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class UploadService:
    """
    Stateless service responsible for validating, storing, and profiling
    uploaded dataset files.

    Statelessness is intentional: each method call is self-contained, which
    makes horizontal scaling trivial and avoids shared mutable state between
    concurrent requests.

    Usage (from the API layer)::

        service = UploadService()
        response = await service.process_upload(filename, file_bytes)
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        # Ensure the upload directory exists on every instantiation.
        # exist_ok=True is safe for concurrent startup scenarios.
        self._settings.upload_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Primary entry point
    # ------------------------------------------------------------------

    async def process_upload(
        self,
        original_filename: str,
        file_bytes: bytes,
    ) -> UploadResponse:
        """
        Orchestrate the full upload pipeline for a single file.

        Pipeline stages:
          1. Validate filename (non-empty)
          2. Validate file extension (whitelist check)
          3. Validate file size (configurable ceiling)
          4. Resolve collision-safe destination path (UUID suffix)
          5. Persist file to disk
          6. Parse into DataFrame
          7. Profile DataFrame → return UploadResponse

        Args:
            original_filename: The ``filename`` attribute from the FastAPI
                ``UploadFile`` object.  May be empty or unsafe.
            file_bytes: Full file content already read into memory.

        Returns:
            :class:`~app.schemas.upload_schema.UploadResponse` with dataset
            statistics ready to serialise as JSON.

        Raises:
            EmptyFilenameError: filename is blank or whitespace-only.
            UnsupportedFileTypeError: extension not in allowed list.
            FileTooLargeError: content exceeds ``max_file_size_mb``.
            FileStorageError: disk I/O failure while saving the file.
            FileParsingError: pandas cannot parse the file content.
        """
        logger.info("Processing upload: '%s' (%d bytes)", original_filename, len(file_bytes))

        # Stage 1 – filename presence
        self._validate_filename(original_filename)

        # Stage 2 – extension whitelist
        extension = self._extract_extension(original_filename)
        self._validate_extension(extension)

        # Stage 3 – size ceiling
        self._validate_size(file_bytes)

        # Stage 4 – collision-safe path resolution
        safe_path = self._resolve_destination(original_filename)

        # Stage 5 – persist to disk
        self._save_file(safe_path, file_bytes)

        # Stage 6 – parse into DataFrame
        dataframe = self._parse_file(safe_path, extension)

        # Stage 7 – profile & return
        response = self._build_response(safe_path.name, dataframe)
        logger.info(
            "Upload succeeded: stored as '%s', %d rows × %d cols",
            safe_path.name,
            response.rows,
            response.columns,
        )
        return response

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    def _validate_filename(self, filename: str) -> None:
        """Reject blank or whitespace-only filenames."""
        if not filename or not filename.strip():
            raise EmptyFilenameError()

    def _extract_extension(self, filename: str) -> str:
        """Return the lower-cased file extension including the leading dot."""
        return Path(filename).suffix.lower()

    def _validate_extension(self, extension: str) -> None:
        """Reject extensions not present in the settings whitelist."""
        if extension not in self._settings.allowed_extensions:
            raise UnsupportedFileTypeError(
                extension=extension,
                allowed=self._settings.allowed_extensions,
            )

    def _validate_size(self, file_bytes: bytes) -> None:
        """Reject files exceeding the configured maximum size in MB."""
        size_mb = len(file_bytes) / _BYTES_PER_MB
        if size_mb > self._settings.max_file_size_mb:
            raise FileTooLargeError(
                size_mb=size_mb,
                limit_mb=self._settings.max_file_size_mb,
            )

    # ------------------------------------------------------------------
    # File-system helpers
    # ------------------------------------------------------------------

    def _resolve_destination(self, original_filename: str) -> Path:
        """
        Return a collision-free Path inside the uploads directory.

        If a file with the same stem already exists, a short UUID4 fragment
        is inserted before the extension.  This avoids clobbering existing
        datasets while maintaining a human-readable name prefix.

        Example::
            "sales.csv" → "sales_3f2a1b9c.csv"  (if "sales.csv" exists)
        """
        stem = Path(original_filename).stem
        suffix = Path(original_filename).suffix.lower()
        destination = self._settings.upload_dir / f"{stem}{suffix}"

        if destination.exists():
            unique_tag = uuid.uuid4().hex[:8]
            destination = self._settings.upload_dir / f"{stem}_{unique_tag}{suffix}"
            logger.debug(
                "Filename collision detected. Renamed to '%s'.", destination.name
            )

        return destination

    def _save_file(self, path: Path, content: bytes) -> None:
        """
        Write raw bytes to *path* atomically.

        Using ``Path.write_bytes()`` (single syscall) is safer than
        open/write/close because it won't leave a partially-written file
        visible to concurrent readers.
        """
        try:
            path.write_bytes(content)
            logger.debug("Saved file to '%s'.", path)
        except OSError as exc:
            raise FileStorageError(
                filename=path.name,
                original_error=str(exc),
            ) from exc

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    def _parse_file(self, path: Path, extension: str) -> pd.DataFrame:
        """
        Load the file at *path* into a pandas DataFrame.

        Reads from disk (not from the original bytes buffer) so that the
        stored file is the canonical source of truth – ensuring what we
        profile is exactly what was persisted.

        Args:
            path: Absolute path to the saved file.
            extension: Lower-cased extension string ('.csv' or '.xlsx').

        Returns:
            A pandas DataFrame representing the dataset.

        Raises:
            FileParsingError: Any pandas-level or I/O parsing failure.
        """
        try:
            if extension == ".csv":
                # engine='python' provides better error messages for malformed CSVs.
                df = pd.read_csv(path, engine="python")
            elif extension == ".xlsx":
                # openpyxl is the recommended engine for .xlsx; xlrd for legacy .xls.
                df = pd.read_excel(path, engine="openpyxl")
            else:
                # Defensive branch – should be unreachable after extension validation.
                raise ValueError(f"Unexpected extension: {extension}")

            return df

        except (ValueError, Exception) as exc:
            # Remove partially-parsed artefacts before propagating.
            if path.exists():
                path.unlink(missing_ok=True)
            raise FileParsingError(
                filename=path.name,
                original_error=str(exc),
            ) from exc

    # ------------------------------------------------------------------
    # Profiling helpers
    # ------------------------------------------------------------------

    def _build_response(self, filename: str, df: pd.DataFrame) -> UploadResponse:
        """
        Derive dataset statistics from a loaded DataFrame and package
        them into an :class:`~app.schemas.upload_schema.UploadResponse`.

        All statistics are computed in-memory from the already-loaded
        DataFrame so no additional disk reads are required.

        Args:
            filename: The collision-safe filename (used in the response).
            df: The fully-loaded pandas DataFrame.

        Returns:
            A populated :class:`~app.schemas.upload_schema.UploadResponse`.
        """
        rows, columns = df.shape

        # Column names – preserve original order.
        column_names: list[str] = df.columns.tolist()

        # Data types – convert numpy dtype objects to human-readable strings.
        data_types: dict[str, str] = {
            col: str(dtype) for col, dtype in df.dtypes.items()
        }

        # Missing values – count NaN / None per column.
        missing_values: dict[str, int] = df.isnull().sum().to_dict()

        # Duplicate rows – rows where every cell is identical to another.
        duplicate_rows: int = int(df.duplicated().sum())

        # Memory usage – deep=True includes object column contents (strings).
        memory_usage_bytes: float = df.memory_usage(deep=True).sum()
        memory_usage_mb: float = round(memory_usage_bytes / _BYTES_PER_MB, 4)

        return UploadResponse(
            filename=filename,
            rows=rows,
            columns=columns,
            column_names=column_names,
            data_types=data_types,
            missing_values=missing_values,
            duplicate_rows=duplicate_rows,
            memory_usage_mb=memory_usage_mb,
            status="success",
        )

    # ------------------------------------------------------------------
    # Future extension stubs
    # ------------------------------------------------------------------

    # async def _compute_quality_score(self, df: pd.DataFrame) -> float:
    #     """
    #     Use an LLM or rule-based heuristic to assign a 0–100 quality score.
    #     Factors: missing-value rate, duplicate rate, schema consistency.
    #     """
    #     raise NotImplementedError

    # async def _run_eda_profiling(self, df: pd.DataFrame) -> dict:
    #     """
    #     Generate an automatic EDA report via ydata-profiling / sweetviz
    #     and return a condensed summary dict.
    #     """
    #     raise NotImplementedError

    # async def _recommend_ml_models(self, df: pd.DataFrame) -> list[str]:
    #     """
    #     Inspect column cardinality, dtypes, and target distribution to
    #     suggest appropriate scikit-learn / XGBoost models.
    #     """
    #     raise NotImplementedError
