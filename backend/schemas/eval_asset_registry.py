"""Pydantic schemas for the Eval Asset Registry.

Machine-readable manifest models for snapshot assets stored in R2.
Used by the construct evidence anchoring pipeline (Cycle-026a).
"""

import re
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


# Filesystem-safe asset_id: lowercase alphanum, hyphens, underscores only
_ASSET_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


class RegistryFileEntry(BaseModel):
    """A single file within a snapshot asset."""

    path: str = Field(..., min_length=1, description="Relative path within the asset root")
    size_bytes: int = Field(..., ge=0, description="File size in bytes")
    content_hash: str = Field(..., description="SHA-256 hash with 'sha256:' prefix")

    @field_validator("content_hash")
    @classmethod
    def hash_must_have_sha256_prefix(cls, v: str) -> str:
        if not v.startswith("sha256:"):
            raise ValueError(f"content_hash must start with 'sha256:', got: {v[:20]}")
        return v


class DatasetRegistryEntry(BaseModel):
    """A single snapshot asset registered for construct evaluation."""

    asset_id: str = Field(..., min_length=1, description="Filesystem-safe asset identifier")
    asset_class: Literal["benchmark", "standard"] = Field(
        ..., description="Asset classification"
    )
    source_url: str = Field(..., min_length=1, description="Canonical source URL")
    version: str = Field(..., min_length=1, description="Asset version tag")
    license: Optional[str] = None
    retrieved_at: datetime = Field(..., description="UTC timestamp of retrieval")
    content_hash: str = Field(..., description="Top-level SHA-256 hash with 'sha256:' prefix")
    files: list[RegistryFileEntry] = Field(
        ..., min_length=1, description="At least one file required"
    )

    @field_validator("asset_id")
    @classmethod
    def asset_id_must_be_filesystem_safe(cls, v: str) -> str:
        if not _ASSET_ID_PATTERN.match(v):
            raise ValueError(
                f"asset_id must be lowercase alphanumeric with hyphens/underscores, "
                f"starting with alphanumeric. Got: {v!r}"
            )
        return v

    @field_validator("content_hash")
    @classmethod
    def hash_must_have_sha256_prefix(cls, v: str) -> str:
        if not v.startswith("sha256:"):
            raise ValueError(f"content_hash must start with 'sha256:', got: {v[:20]}")
        return v


class DatasetRegistryDocument(BaseModel):
    """Aggregate registry document containing multiple asset entries."""

    version: str = Field(..., min_length=1, description="Registry document version")
    generated_at: datetime = Field(..., description="UTC timestamp of generation")
    entries: list[DatasetRegistryEntry] = Field(
        default_factory=list, description="Registry entries"
    )
