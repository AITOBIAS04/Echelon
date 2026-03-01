"""Configuration module for the OSINT Pipeline.

Loads API keys, timeouts, and registry path from environment variables.
No framework dependencies (no Dynaconf, no pydantic-settings).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


# Default registry path relative to monorepo root
_DEFAULT_REGISTRY_PATH = (
    "theatre/fixtures/two_rail_theatres_v0_1/datasets/"
    "echelon_osint_source_registry_v0_4_0.json"
)


@dataclass(frozen=True)
class PipelineConfig:
    """Immutable pipeline configuration loaded from environment variables.

    Usage::

        config = PipelineConfig.from_env()
        print(config.registry_path)
    """

    # Registry
    registry_path: str = _DEFAULT_REGISTRY_PATH

    # API keys (empty string means not configured)
    companies_house_api_key: str = ""
    sec_edgar_user_agent: str = ""
    fred_api_key: str = ""

    # Parallelism
    max_workers: int = 5
    timeout_budget: float = 60.0
    collector_timeout: float = 30.0

    @classmethod
    def from_env(cls) -> PipelineConfig:
        """Load configuration from environment variables."""
        return cls(
            registry_path=os.environ.get(
                "OSINT_REGISTRY_PATH", _DEFAULT_REGISTRY_PATH
            ),
            companies_house_api_key=os.environ.get(
                "COMPANIES_HOUSE_API_KEY", ""
            ),
            sec_edgar_user_agent=os.environ.get(
                "SEC_EDGAR_USER_AGENT", ""
            ),
            fred_api_key=os.environ.get("FRED_API_KEY", ""),
            max_workers=int(os.environ.get("OSINT_MAX_WORKERS", "5")),
            timeout_budget=float(
                os.environ.get("OSINT_TIMEOUT_BUDGET", "60.0")
            ),
            collector_timeout=float(
                os.environ.get("OSINT_COLLECTOR_TIMEOUT", "30.0")
            ),
        )

    def collector_configs(self) -> dict[str, dict[str, str]]:
        """Return per-collector config dicts for initialisation."""
        configs: dict[str, dict[str, str]] = {}

        if self.companies_house_api_key:
            configs["companies_house_api"] = {
                "api_key": self.companies_house_api_key,
            }

        if self.sec_edgar_user_agent:
            configs["sec_edgar"] = {
                "user_agent": self.sec_edgar_user_agent,
            }

        if self.fred_api_key:
            configs["fred_api"] = {
                "api_key": self.fred_api_key,
            }

        # No-auth collectors always available
        configs["ecb_data_api"] = {}
        configs["boe_rates"] = {}
        configs["uk_gazette"] = {}

        return configs
