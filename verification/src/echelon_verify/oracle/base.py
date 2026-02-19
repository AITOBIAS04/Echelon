"""Oracle adapter abstract base class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from echelon_verify.config import OracleConfig
    from echelon_verify.models import GroundTruthRecord, OracleOutput


class OracleAdapter(ABC):
    """Interface for oracle construct invocation."""

    @abstractmethod
    async def invoke(
        self, ground_truth: GroundTruthRecord, follow_up_question: str
    ) -> OracleOutput:
        """Invoke the oracle with a ground truth record and capture output."""

    @classmethod
    def from_config(cls, config: OracleConfig) -> OracleAdapter:
        """Factory method to create adapter from config."""
        if config.type == "http":
            from echelon_verify.oracle.http_adapter import HttpOracleAdapter

            return HttpOracleAdapter(config)
        elif config.type == "python":
            from echelon_verify.oracle.python_adapter import PythonOracleAdapter

            return PythonOracleAdapter(config)
        raise ValueError(f"Unknown oracle type: {config.type}")
