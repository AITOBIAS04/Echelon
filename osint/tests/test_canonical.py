"""
Tests for canonical JSON and HTTP transcript receipt hashing.

Key invariant: two independent fetchers with identical inputs
MUST produce identical receipt hashes.
"""

import json
import sys
import os

# Add osint/ directory to path so osint_pipeline package is found here.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from osint_pipeline.engine.canonical import (
    canonical_json,
    canonical_hash,
    sha256_hex,
    http_transcript_canonical,
    http_transcript_hash,
)


def test_canonical_json_sorted_keys():
    """Keys must be sorted lexicographically."""
    obj = {"z": 1, "a": 2, "m": 3}
    result = canonical_json(obj)
    assert result == '{"a":2,"m":3,"z":1}'


def test_canonical_json_no_whitespace():
    """No whitespace between separators."""
    obj = {"key": "value", "num": 42}
    result = canonical_json(obj)
    assert " " not in result.replace('"key"', "").replace('"value"', "")


def test_canonical_json_nested():
    """Nested objects have sorted keys at all levels."""
    obj = {"outer": {"z": 1, "a": 2}, "inner": [3, 2, 1]}
    result = canonical_json(obj)
    parsed = json.loads(result)
    assert list(parsed.keys()) == ["inner", "outer"]
    assert list(parsed["outer"].keys()) == ["a", "z"]


def test_sha256_string():
    """SHA-256 of empty string is known constant."""
    result = sha256_hex("")
    assert result == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert len(result) == 64


def test_sha256_bytes():
    """SHA-256 accepts bytes directly."""
    result = sha256_hex(b"hello")
    assert result == sha256_hex("hello")


def test_canonical_hash():
    """canonical_hash = sha256(canonical_json(obj))."""
    obj = {"b": 2, "a": 1}
    expected = sha256_hex(canonical_json(obj))
    assert canonical_hash(obj) == expected


def test_http_transcript_canonical_form():
    """Verify the canonical form matches spec (Composed Oracle Spec v2 §5)."""
    canonical = http_transcript_canonical(
        method="GET",
        url="https://api.example.com/data",
        headers={"Accept": "application/json", "Authorization": "Bearer xyz"},
        response_status=200,
        response_body=b'{"result": true}',
        timestamp_ms=1709251200000,
    )
    lines = canonical.split("\n")
    assert lines[0] == "GET"
    assert lines[1] == "https://api.example.com/data"
    # Headers filtered to allowlist then sorted by lowercase key
    assert lines[2] == "accept=application/json"
    assert lines[3] == "200"
    assert len(lines[4]) == 64  # body hash
    assert lines[5] == "1709251200000"


def test_http_transcript_determinism():
    """Same inputs → same receipt hash. This is the critical invariant."""
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


def test_http_transcript_header_order_irrelevant():
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


def test_http_transcript_url_trailing_slash():
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


def test_different_body_different_hash():
    """Different response bodies must produce different receipt hashes."""
    base = dict(
        method="GET", url="https://api.example.com/test",
        headers={}, response_status=200, timestamp_ms=1000,
    )
    hash_a = http_transcript_hash(**base, response_body=b"body_a")
    hash_b = http_transcript_hash(**base, response_body=b"body_b")
    assert hash_a != hash_b


def test_different_timestamp_different_hash():
    """Different timestamps must produce different receipt hashes."""
    base = dict(
        method="GET", url="https://api.example.com/test",
        headers={}, response_status=200, response_body=b"same",
    )
    hash_a = http_transcript_hash(**base, timestamp_ms=1000)
    hash_b = http_transcript_hash(**base, timestamp_ms=2000)
    assert hash_a != hash_b


if __name__ == "__main__":
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS: {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {test.__name__} — {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {test.__name__} — {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed, {passed + failed} total")
    sys.exit(1 if failed > 0 else 0)
