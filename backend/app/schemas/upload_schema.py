"""
schemas/upload_schema.py
========================
Pydantic models that define the contract between the API layer
and its consumers (Swagger UI, external clients, future React frontend).

Architectural note:
  Keeping schemas decoupled from ORM models lets us evolve the database
  schema independently from the public API surface – critical for a
  long-lived SaaS product.

Future extension points:
  - DataQualitySchema  : AI-powered quality scores
  - ProfileReportSchema: Automatic EDA / YData-Profiling output
  - MLRecommendation   : Suggested models based on detected dtypes/cardinality
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Upload Response
# ---------------------------------------------------------------------------

class UploadResponse(BaseModel):
    """
    Returned to the caller after a successful file upload and analysis pass.

    Every field is explicitly typed so downstream consumers (TypeScript,
    OpenAPI codegen) receive a fully-specified contract.
    """

    filename: str = Field(
        ...,
        description="The final filename stored on disk (may differ from the "
                    "original if a UUID suffix was appended to avoid conflicts).",
        examples=["sales_data_3f2a.csv"],
    )
    rows: int = Field(
        ...,
        ge=0,
        description="Total number of data rows (excluding the header).",
        examples=[1200],
    )
    columns: int = Field(
        ...,
        ge=0,
        description="Number of columns in the dataset.",
        examples=[14],
    )
    column_names: list[str] = Field(
        ...,
        description="Ordered list of column header names.",
        examples=[["date", "revenue", "region"]],
    )
    data_types: dict[str, str] = Field(
        ...,
        description="Mapping of column name → inferred pandas dtype string.",
        examples=[{"date": "object", "revenue": "float64", "region": "object"}],
    )
    missing_values: dict[str, int] = Field(
        ...,
        description="Mapping of column name → count of null / NaN cells.",
        examples=[{"date": 0, "revenue": 3, "region": 0}],
    )
    duplicate_rows: int = Field(
        ...,
        ge=0,
        description="Number of fully-duplicate rows detected in the dataset.",
        examples=[7],
    )
    memory_usage_mb: float = Field(
        ...,
        ge=0.0,
        description="Approximate in-memory size of the loaded DataFrame (MB).",
        examples=[0.42],
    )
    status: str = Field(
        default="success",
        description="High-level result indicator. Always 'success' on HTTP 200.",
        examples=["success"],
    )

    # -----------------------------------------------------------------------
    # Extension stubs – uncomment as features are implemented
    # -----------------------------------------------------------------------
    # quality_score: float | None = Field(
    #     None,
    #     description="AI-computed data quality score (0–100).",
    # )
    # eda_summary: dict[str, Any] | None = Field(
    #     None,
    #     description="Automatic EDA highlights (skewness, outlier counts, etc.).",
    # )
    # ml_recommendations: list[str] | None = Field(
    #     None,
    #     description="Suggested ML algorithms based on dataset profile.",
    # )

    model_config = {
        "json_schema_extra": {
            "example": {
                "filename": "q1_sales_a1b2.csv",
                "rows": 5000,
                "columns": 12,
                "column_names": ["id", "date", "product", "revenue"],
                "data_types": {"id": "int64", "date": "object", "revenue": "float64"},
                "missing_values": {"id": 0, "date": 0, "revenue": 14},
                "duplicate_rows": 3,
                "memory_usage_mb": 1.82,
                "status": "success",
            }
        }
    }


# ---------------------------------------------------------------------------
# Error Response (used by exception handlers in main.py)
# ---------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    """
    Standardised error envelope returned on all 4xx / 5xx responses.

    Having a single error schema across the API lets frontend teams write
    one generic error-handling hook rather than parsing ad-hoc structures.
    """

    detail: str = Field(
        ...,
        description="Human-readable description of what went wrong.",
        examples=["File type '.txt' is not supported. Accepted types: .csv, .xlsx"],
    )
    error_code: str = Field(
        ...,
        description="Machine-readable slug for programmatic error handling.",
        examples=["UNSUPPORTED_FILE_TYPE"],
    )
    status: str = Field(
        default="error",
        description="Always 'error' for non-200 responses.",
    )
