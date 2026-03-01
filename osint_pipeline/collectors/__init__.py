"""Collectors — source-specific fetch + extract implementations."""

from osint_pipeline.collectors.base import BaseCollector
from osint_pipeline.collectors.boe import BoECollector
from osint_pipeline.collectors.companies_house import CompaniesHouseCollector
from osint_pipeline.collectors.ecb_sdmx import ECBDataCollector
from osint_pipeline.collectors.fred import FREDCollector
from osint_pipeline.collectors.gazette import GazetteCollector
from osint_pipeline.collectors.sec_edgar import SECEdgarCollector
