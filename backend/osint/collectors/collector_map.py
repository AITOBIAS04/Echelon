"""Collector map — registry of all available OSINT collectors.

Provides build_collector_map() which returns a dict of source_id -> BaseCollector
for use by CollectionRunner. All Batch 1 collectors are registered here.
"""
from __future__ import annotations

from backend.osint.collectors.base import BaseCollector
from backend.osint.collectors.alpha_vantage import AlphaVantageCollector
from backend.osint.models.evidence import WMDomain
from backend.osint.collectors.calendarific import CalendarificCollector
from backend.osint.collectors.carbon_intensity import CarbonIntensityCollector
from backend.osint.collectors.coingecko import CoinGeckoCollector
from backend.osint.collectors.companies_house import CompaniesHouseCollector
from backend.osint.collectors.etherscan import EtherscanCollector
from backend.osint.collectors.fred import FREDCollector
from backend.osint.collectors.openaq import OpenAQCollector
from backend.osint.collectors.opencorporates import OpenCorporatesCollector
from backend.osint.collectors.opensky import OpenSkyCollector
from backend.osint.collectors.semantic_scholar import SemanticScholarCollector
from backend.osint.collectors.usgs_earthquake import USGSEarthquakeCollector
from backend.osint.collectors.worldmonitor import WorldMonitorCollector


def build_collector_map() -> dict[str, BaseCollector]:
    """Build the complete source_id -> BaseCollector mapping.

    Instantiates all available collectors. API keys are read from
    environment variables at construction time (per-collector convention).

    Returns dict suitable for CollectionRunner(collectors=...).
    """
    collectors: list[BaseCollector] = [
        # ── Existing collectors ──
        WorldMonitorCollector(domain=WMDomain.INTELLIGENCE),
        WorldMonitorCollector(domain=WMDomain.MARKET),
        WorldMonitorCollector(domain=WMDomain.MARITIME),
        CompaniesHouseCollector(),
        # ── Cycle-026 Batch 1: Financial + Corporate ──
        FREDCollector(),
        AlphaVantageCollector(),
        OpenCorporatesCollector(),
        EtherscanCollector(),
        # ── Cycle-026 Batch 1: Crypto + Geospatial ──
        CoinGeckoCollector(),
        OpenSkyCollector(),
        # ── Cycle-026 Batch 1: Science + Environment ──
        USGSEarthquakeCollector(),
        CarbonIntensityCollector(),
        OpenAQCollector(),
        # ── Cycle-026 Batch 1: Counter-signal ──
        CalendarificCollector(),
        # ── Cycle-026b: Research evidence ──
        SemanticScholarCollector(),
    ]
    return {c.source_id(): c for c in collectors}
