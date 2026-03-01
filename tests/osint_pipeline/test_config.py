"""Tests for the OSINT Pipeline configuration module."""

from __future__ import annotations

import os

import pytest

from osint_pipeline.config import PipelineConfig


class TestPipelineConfigDefaults:
    """Test default configuration values."""

    def test_default_registry_path(self):
        config = PipelineConfig()
        assert "echelon_osint_source_registry_v0_6_0.json" in config.registry_path

    def test_default_max_workers(self):
        config = PipelineConfig()
        assert config.max_workers == 5

    def test_default_timeout_budget(self):
        config = PipelineConfig()
        assert config.timeout_budget == 60.0

    def test_default_collector_timeout(self):
        config = PipelineConfig()
        assert config.collector_timeout == 30.0

    def test_default_api_keys_empty(self):
        config = PipelineConfig()
        assert config.companies_house_api_key == ""
        assert config.sec_edgar_user_agent == ""
        assert config.fred_api_key == ""


class TestPipelineConfigFromEnv:
    """Test configuration loading from environment variables."""

    def test_loads_registry_path(self, monkeypatch):
        monkeypatch.setenv("OSINT_REGISTRY_PATH", "/custom/registry.json")
        config = PipelineConfig.from_env()
        assert config.registry_path == "/custom/registry.json"

    def test_loads_api_keys(self, monkeypatch):
        monkeypatch.setenv("COMPANIES_HOUSE_API_KEY", "ch_key_123")
        monkeypatch.setenv("SEC_EDGAR_USER_AGENT", "App test@test.com")
        monkeypatch.setenv("FRED_API_KEY", "fred_key_456")
        config = PipelineConfig.from_env()
        assert config.companies_house_api_key == "ch_key_123"
        assert config.sec_edgar_user_agent == "App test@test.com"
        assert config.fred_api_key == "fred_key_456"

    def test_loads_numeric_settings(self, monkeypatch):
        monkeypatch.setenv("OSINT_MAX_WORKERS", "10")
        monkeypatch.setenv("OSINT_TIMEOUT_BUDGET", "120.0")
        monkeypatch.setenv("OSINT_COLLECTOR_TIMEOUT", "45.0")
        config = PipelineConfig.from_env()
        assert config.max_workers == 10
        assert config.timeout_budget == 120.0
        assert config.collector_timeout == 45.0

    def test_defaults_when_env_not_set(self, monkeypatch):
        # Clear any potentially set vars
        for var in [
            "OSINT_REGISTRY_PATH", "COMPANIES_HOUSE_API_KEY",
            "SEC_EDGAR_USER_AGENT", "FRED_API_KEY",
            "OSINT_MAX_WORKERS", "OSINT_TIMEOUT_BUDGET",
            "OSINT_COLLECTOR_TIMEOUT",
        ]:
            monkeypatch.delenv(var, raising=False)
        config = PipelineConfig.from_env()
        assert config.max_workers == 5
        assert config.timeout_budget == 60.0


class TestPipelineConfigCollectorConfigs:
    """Test collector config generation."""

    def test_no_auth_collectors_always_present(self):
        config = PipelineConfig()
        configs = config.collector_configs()
        assert "ecb_data_api" in configs
        assert "boe_rates" in configs
        assert "uk_gazette" in configs

    def test_auth_collectors_only_with_keys(self):
        config = PipelineConfig()
        configs = config.collector_configs()
        assert "companies_house_api" not in configs
        assert "sec_edgar" not in configs
        assert "fred_api" not in configs

    def test_auth_collectors_present_with_keys(self):
        config = PipelineConfig(
            companies_house_api_key="key1",
            sec_edgar_user_agent="App user@x.com",
            fred_api_key="key2",
        )
        configs = config.collector_configs()
        assert configs["companies_house_api"]["api_key"] == "key1"
        assert configs["sec_edgar"]["user_agent"] == "App user@x.com"
        assert configs["fred_api"]["api_key"] == "key2"

    def test_frozen_dataclass(self):
        config = PipelineConfig()
        with pytest.raises(AttributeError):
            config.max_workers = 99


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
