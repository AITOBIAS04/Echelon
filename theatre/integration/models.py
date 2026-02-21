"""Integration models — PR-specific data structures for Observer verification."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class GroundTruthRecord(BaseModel):
    """A GitHub PR used as ground truth for oracle verification.

    Maps to echelon-verify's GroundTruthRecord specification.
    """

    id: str
    title: str
    description: str = ""
    diff_content: str = ""
    files_changed: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    labels: list[str] = Field(default_factory=list)
    author: str = ""
    url: str = ""
    repo: str = ""


class OracleOutput(BaseModel):
    """Structured output from an oracle construct invocation.

    Contains the oracle's summary, claims, and follow-up response.
    """

    ground_truth_id: str
    summary: str
    key_claims: list[str] = Field(default_factory=list)
    follow_up_question: str = ""
    follow_up_response: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    invoked_at: datetime = Field(default_factory=datetime.utcnow)
    latency_ms: int = 0
