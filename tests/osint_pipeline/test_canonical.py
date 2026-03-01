"""Tests for canonical JSON and HTTP transcript receipt hashing.

Key invariant: two independent fetchers with identical inputs
MUST produce identical receipt hashes.

T1.2: verifies delegation to theatre engine produces same hash,
SHA-256 known constants, HTTP transcript form structure,
receipt determinism, header order irrelevance, trailing slash
normalisation, different body/timestamp yield different hashes.
"""

from __future__ import annotations

import json

from osint_pipeline.engine.canonical import (
    CANONICAL_HEADER_ALLOWLIST,
    canonical_hash,
    canonical_json,
    http_transcript_canonical,
    http_transcript_hash,
    sha256_hex,
)
from theatre.engine.canonical_json import canonical_json as theatre_canonical_json


class TestCanonicalJsonDelegation:
    """Verify that canonical_json delegates to theatre engine."""

    def test_same_function(self):
        """canonical_json IS the theatre engine function."""
        assert canonical_json is theatre_canonical_json

    def test_same_output(self):
        """Same input produces identical output from both paths."""
        obj = {"z": 1, "a": 2, "nested": {"b": True, "a": None}}
        assert canonical_json(obj) == theatre_canonical_json(obj)

    def test_float_normalisation(self):
        """Theatre engine normalises floats (1.0 -> 1)."""
        result = canonical_json({"val": 1.0})
        assert result == '{"val":1}'

    def test_sorted_keys(self):
        """Keys sorted lexicographically at every level."""
        obj = {"z": 1, "a": 2, "m": 3}
        result = canonical_json(obj)
        assert result == '{"a":2,"m":3,"z":1}'

    def test_no_whitespace(self):
        """No whitespace between separators."""
        obj = {"key": "value", "num": 42}
        result = canonical_json(obj)
        # Check no spaces between tokens (except inside string values)
        assert '" :' not in result
        assert '", ' not in result

    def test_nested_sorted(self):
        """Nested objects have sorted keys at all levels."""
        obj = {"outer": {"z": 1, "a": 2}, "inner": [3, 2, 1]}
        result = canonical_json(obj)
        parsed = json.loads(result)
        assert list(parsed.keys()) == ["inner", "outer"]
        assert list(parsed["outer"].keys()) == ["a", "z"]


class TestSHA256:
    """SHA-256 utility tests."""

    def test_empty_string(self):
        """SHA-256 of empty string is known constant."""
        result = sha256_hex("")
        assert result == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert len(result) == 64

    def test_bytes_input(self):
        """SHA-256 accepts bytes directly."""
        assert sha256_hex(b"hello") == sha256_hex("hello")

    def test_canonical_hash(self):
        """canonical_hash = sha256(canonical_json(obj))."""
        obj = {"b": 2, "a": 1}
        expected = sha256_hex(canonical_json(obj))
        assert canonical_hash(obj) == expected


class TestHTTPTranscriptCanonical:
    """HTTP Transcript Canonical Form tests."""

    def test_canonical_form_structure(self):
        """Verify the canonical form matches spec (6-field)."""
        canonical = http_transcript_canonical(
            method="GET",
            url="https://api.example.com/data",
            headers={"Accept": "application/json", "Authorization": "Bearer xyz"},
            response_status=200,
            response_body=b'{"result": true}',
            timestamp_ms=1709251200000,
        )
        lines = canonical.split("\n")
        assert len(lines) == 6
        assert lines[0] == "GET"
        assert lines[1] == "https://api.example.com/data"
        # Authorization filtered out by allowlist
        assert lines[2] == "accept=application/json"
        assert lines[3] == "200"
        assert len(lines[4]) == 64  # body hash
        assert lines[5] == "1709251200000"

    def test_determinism(self):
        """Same inputs -> same receipt hash."""
        params = dict(
            method="GET",
            url="https://api.company-information.service.gov.uk/company/12345678",
            headers={"Accept": "application/json", "Authorization": "Basic abc123"},
            response_status=200,
            response_body=b'{"company_name":"Test Ltd","company_number":"12345678"}',
            timestamp_ms=1709251200000,
        )
        hash1 = http_transcript_hash(**params)
        hash2 = http_transcript_hash(**params)
        assert hash1 == hash2
        assert len(hash1) == 64

    def test_header_order_irrelevant(self):
        """Header insertion order must not affect receipt hash."""
        params_a = dict(
            method="GET",
            url="https://api.example.com/test",
            headers={"Zebra": "last", "Accept": "first", "Middle": "mid"},
            response_status=200,
            response_body=b"test",
            timestamp_ms=1000,
        )
        params_b = dict(
            method="GET",
            url="https://api.example.com/test",
            headers={"Accept": "first", "Middle": "mid", "Zebra": "last"},
            response_status=200,
            response_body=b"test",
            timestamp_ms=1000,
        )
        assert http_transcript_hash(**params_a) == http_transcript_hash(**params_b)

    def test_trailing_slash_stripped(self):
        """Trailing slash is stripped for canonical form."""
        params_a = dict(
            method="GET", url="https://api.example.com/test/",
            headers={}, response_status=200, response_body=b"x", timestamp_ms=1000,
        )
        params_b = dict(
            method="GET", url="https://api.example.com/test",
            headers={}, response_status=200, response_body=b"x", timestamp_ms=1000,
        )
        assert http_transcript_hash(**params_a) == http_transcript_hash(**params_b)

    def test_different_body_different_hash(self):
        """Different response bodies must produce different receipt hashes."""
        base = dict(
            method="GET", url="https://api.example.com/test",
            headers={}, response_status=200, timestamp_ms=1000,
        )
        hash_a = http_transcript_hash(**base, response_body=b"body_a")
        hash_b = http_transcript_hash(**base, response_body=b"body_b")
        assert hash_a != hash_b

    def test_different_timestamp_different_hash(self):
        """Different timestamps must produce different receipt hashes."""
        base = dict(
            method="GET", url="https://api.example.com/test",
            headers={}, response_status=200, response_body=b"same",
        )
        hash_a = http_transcript_hash(**base, timestamp_ms=1000)
        hash_b = http_transcript_hash(**base, timestamp_ms=2000)
        assert hash_a != hash_b

    def test_different_auth_headers_same_hash(self):
        """Two requests with different Authorization headers -> identical hashes."""
        base = dict(
            method="GET",
            url="https://api.example.com/data",
            response_status=200,
            response_body=b'{"result": true}',
            timestamp_ms=1709251200000,
        )
        hash_a = http_transcript_hash(
            **base,
            headers={"Accept": "application/json", "Authorization": "Bearer token_a"},
        )
        hash_b = http_transcript_hash(
            **base,
            headers={"Accept": "application/json", "Authorization": "Bearer token_b"},
        )
        assert hash_a == hash_b

    def test_url_query_params_order_irrelevant(self):
        """URL query params in different order -> identical hashes."""
        base = dict(
            method="GET",
            headers={"Accept": "application/json"},
            response_status=200,
            response_body=b'{"result": true}',
            timestamp_ms=1709251200000,
        )
        hash_a = http_transcript_hash(
            **base,
            url="https://api.example.com/search?q=test&page=1",
        )
        hash_b = http_transcript_hash(
            **base,
            url="https://api.example.com/search?page=1&q=test",
        )
        assert hash_a == hash_b

    def test_header_allowlist(self):
        """Only allowlisted headers appear in canonical form."""
        assert "accept" in CANONICAL_HEADER_ALLOWLIST
        assert "content-type" in CANONICAL_HEADER_ALLOWLIST
        assert "user-agent" in CANONICAL_HEADER_ALLOWLIST
        assert "authorization" not in CANONICAL_HEADER_ALLOWLIST
        assert "cookie" not in CANONICAL_HEADER_ALLOWLIST
        assert "x-request-id" not in CANONICAL_HEADER_ALLOWLIST


class TestAuthRedaction:
    """E3: Auth + receipt redaction regression tests.

    Verifies that api_key material is stripped from canonical forms
    and receipt hashes are identical with or without auth headers.
    """

    def test_auth_headers_stripped_from_canonical(self):
        """Authorization and X-Api-Key are absent from canonical form."""
        with_auth = http_transcript_canonical(
            method="GET",
            url="https://api.bls.gov/publicAPI/v2/timeseries/data/",
            headers={
                "Authorization": "Bearer secret",
                "X-Api-Key": "key123",
                "Accept": "application/json",
            },
            response_status=200,
            response_body=b'{"status":"OK"}',
            timestamp_ms=1709251200000,
        )
        without_auth = http_transcript_canonical(
            method="GET",
            url="https://api.bls.gov/publicAPI/v2/timeseries/data/",
            headers={"Accept": "application/json"},
            response_status=200,
            response_body=b'{"status":"OK"}',
            timestamp_ms=1709251200000,
        )
        assert with_auth == without_auth

    def test_secret_material_absent(self):
        """Secret values never appear in canonical form."""
        canonical = http_transcript_canonical(
            method="GET",
            url="https://api.example.com/data",
            headers={
                "Authorization": "Bearer secret",
                "X-Api-Key": "key123",
                "Accept": "application/json",
            },
            response_status=200,
            response_body=b"{}",
            timestamp_ms=1000,
        )
        assert "secret" not in canonical
        assert "key123" not in canonical
        assert "Bearer" not in canonical

    def test_receipt_hash_identical_with_without_auth(self):
        """Receipt hashes are identical regardless of auth headers."""
        base = dict(
            method="GET",
            url="https://api.bls.gov/publicAPI/v2/timeseries/data/",
            response_status=200,
            response_body=b'{"status":"OK"}',
            timestamp_ms=1709251200000,
        )
        hash_with = http_transcript_hash(
            **base,
            headers={
                "Authorization": "Bearer secret",
                "X-Api-Key": "key123",
                "Accept": "application/json",
            },
        )
        hash_without = http_transcript_hash(
            **base,
            headers={"Accept": "application/json"},
        )
        assert hash_with == hash_without
