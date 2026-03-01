"""Tests for the OSINT Pipeline CLI module."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from osint_pipeline.cli import main, _parse_query


class TestParseQuery:
    """Test query JSON parsing."""

    def test_valid_json(self):
        result = _parse_query('{"key": "value"}')
        assert result == {"key": "value"}

    def test_invalid_json_exits(self):
        with pytest.raises(SystemExit):
            _parse_query("not json")

    def test_non_dict_exits(self):
        with pytest.raises(SystemExit):
            _parse_query("[1, 2, 3]")


class TestCLIHelp:
    """Test CLI help and basic argument handling."""

    def test_no_args_shows_help(self, capsys):
        result = main([])
        assert result == 0

    def test_unknown_command(self):
        # argparse will error on unknown command
        with pytest.raises(SystemExit):
            main(["nonexistent"])


class TestCLIInspect:
    """Test CLI inspect command."""

    def test_inspect_valid_file(self, capsys):
        data = {"oracle_id": "test-123", "composite_score": 0.85}
        with tempfile.NamedTemporaryFile(
            suffix=".json", mode="w", delete=False
        ) as f:
            json.dump(data, f)
            f.flush()
            result = main(["inspect", "--bundle", f.name])
        assert result == 0
        captured = capsys.readouterr()
        assert "test-123" in captured.out

    def test_inspect_missing_file(self, capsys):
        result = main(["inspect", "--bundle", "/nonexistent/file.json"])
        assert result == 1

    def test_inspect_invalid_json(self, capsys):
        with tempfile.NamedTemporaryFile(
            suffix=".json", mode="w", delete=False
        ) as f:
            f.write("not json")
            f.flush()
            result = main(["inspect", "--bundle", f.name])
        assert result == 1


class TestCLIValidate:
    """Test CLI validate command."""

    def test_validate_missing_registry(self, capsys):
        result = main(["validate", "--registry", "/nonexistent/reg.json"])
        assert result == 1

    def test_validate_actual_registry(self, capsys):
        registry_path = (
            "theatre/fixtures/two_rail_theatres_v0_1/datasets/"
            "echelon_osint_source_registry_v0_4_0.json"
        )
        if not Path(registry_path).exists():
            pytest.skip("Registry fixture not available")
        result = main(["validate", "--registry", registry_path])
        assert result == 0
        captured = capsys.readouterr()
        assert "Sources:" in captured.out


class TestCLICollect:
    """Test CLI collect command."""

    def test_collect_unknown_source(self, capsys):
        result = main([
            "collect", "--source", "nonexistent_source",
            "--query", '{"test": true}',
        ])
        assert result == 1
        captured = capsys.readouterr()
        assert "Unknown source" in captured.err

    def test_collect_missing_api_key(self, capsys, monkeypatch):
        # Clear env to ensure no key
        monkeypatch.delenv("COMPANIES_HOUSE_API_KEY", raising=False)
        result = main([
            "collect", "--source", "companies_house_api",
            "--query", '{"company_number": "12345678"}',
        ])
        assert result == 1


class TestCLIRun:
    """Test CLI run command — basic argument validation only."""

    def test_run_requires_theatre(self):
        with pytest.raises(SystemExit):
            main(["run", "--query", '{"test": true}'])

    def test_run_requires_query(self):
        with pytest.raises(SystemExit):
            main(["run", "--theatre", "TEST"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
