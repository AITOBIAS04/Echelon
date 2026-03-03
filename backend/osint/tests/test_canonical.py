"""Canonical hashing tests — determinism, edge cases, cross-verification.

Tests verify that Echelon Canonical JSON v0 produces deterministic output
with sorted keys and compact separators, and that re-exported wrappers
produce identical output to the API contract originals.
"""
from __future__ import annotations

from backend.osint.canonical import canonical_json, compute_content_hash, compute_receipt_hash
from backend.schemas.worldmonitor_api_contract import (
    canonical_json as contract_canonical_json,
    compute_receipt_hash as contract_compute_receipt_hash,
)


class TestCanonicalJson:
    """Echelon Canonical JSON v0 determinism and correctness."""

    def test_deterministic_same_input(self) -> None:
        """Same input dict produces same output string."""
        obj = {"b": 2, "a": 1, "c": 3}
        result1 = canonical_json(obj)
        result2 = canonical_json(obj)
        assert result1 == result2

    def test_sorted_keys(self) -> None:
        """Keys are sorted alphabetically."""
        obj = {"zebra": 1, "apple": 2, "mango": 3}
        result = canonical_json(obj)
        assert result == '{"apple":2,"mango":3,"zebra":1}'

    def test_compact_separators(self) -> None:
        """No spaces after : or , separators."""
        obj = {"a": 1, "b": 2}
        result = canonical_json(obj)
        assert " " not in result
        assert result == '{"a":1,"b":2}'

    def test_unicode_preserved(self) -> None:
        """Unicode characters preserved (no ASCII escape)."""
        obj = {"city": "Tehr\u0101n", "script": "\u0641\u0627\u0631\u0633\u06cc"}
        result = canonical_json(obj)
        assert "Tehr\u0101n" in result
        assert "\u0641\u0627\u0631\u0633\u06cc" in result
        # Should NOT contain \\u escape sequences
        assert "\\u" not in result

    def test_nested_sorted(self) -> None:
        """Nested dicts and lists sorted correctly."""
        obj = {"b": {"z": 26, "a": 1}, "a": [3, 1, 2]}
        result = canonical_json(obj)
        assert result == '{"a":[3,1,2],"b":{"a":1,"z":26}}'

    def test_empty_dict(self) -> None:
        """Empty dict produces '{}'."""
        assert canonical_json({}) == "{}"

    def test_deeply_nested(self) -> None:
        """Deeply nested structures are sorted at every level."""
        obj = {"z": {"y": {"x": {"w": 1, "v": 2}}}}
        result = canonical_json(obj)
        assert result == '{"z":{"y":{"x":{"v":2,"w":1}}}}'


class TestComputeContentHash:
    """SHA-256 of raw response bytes."""

    def test_deterministic(self) -> None:
        """Same bytes produce same hash."""
        payload = b'{"key":"value"}'
        h1 = compute_content_hash(payload)
        h2 = compute_content_hash(payload)
        assert h1 == h2
        assert len(h1) == 64

    def test_different_bytes_different_hash(self) -> None:
        """Different bytes produce different hash."""
        h1 = compute_content_hash(b'{"a":1}')
        h2 = compute_content_hash(b'{"a":2}')
        assert h1 != h2

    def test_empty_bytes(self) -> None:
        """Empty bytes produce the SHA-256 of empty string."""
        h = compute_content_hash(b"")
        assert len(h) == 64
        # Known SHA-256 of empty string
        assert h == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    def test_bytes_vs_dict_distinction(self) -> None:
        """Bytes-based hash differs from API contract dict-based hash.

        compute_content_hash(bytes) hashes raw bytes.
        API contract's compute_content_hash(dict) re-serialises via canonical_json.
        These are intentionally different — no equality assertion.
        """
        from backend.schemas.worldmonitor_api_contract import (
            compute_content_hash as contract_hash,
        )
        payload_dict = {"b": 2, "a": 1}
        # Contract hashes canonical_json(dict) — sorted keys, compact
        contract_result = contract_hash(payload_dict)
        # Our function hashes raw bytes — could be any serialisation
        raw_bytes = b'{"b": 2, "a": 1}'  # Note: different from canonical form
        our_result = compute_content_hash(raw_bytes)
        # They SHOULD differ because the byte representations differ
        assert contract_result != our_result


class TestComputeReceiptHash:
    """SHA-256 of canonical HTTP transcript."""

    def test_deterministic(self) -> None:
        """Same inputs produce same hash."""
        h1 = compute_receipt_hash("POST", "http://localhost/api", "q=1", "h:v", "abc" * 22)
        h2 = compute_receipt_hash("POST", "http://localhost/api", "q=1", "h:v", "abc" * 22)
        assert h1 == h2
        assert len(h1) == 64

    def test_different_inputs_different_hash(self) -> None:
        """Different parameters produce different hash."""
        h1 = compute_receipt_hash("GET", "http://a.com", "", "", "hash1" + "0" * 59)
        h2 = compute_receipt_hash("POST", "http://a.com", "", "", "hash1" + "0" * 59)
        assert h1 != h2

    def test_method_case_insensitive(self) -> None:
        """Method is uppercased — 'get' and 'GET' produce same hash."""
        h1 = compute_receipt_hash("get", "http://x.com", "", "", "h" * 64)
        h2 = compute_receipt_hash("GET", "http://x.com", "", "", "h" * 64)
        assert h1 == h2


class TestCrossVerification:
    """Re-exported wrappers match API contract originals."""

    def test_canonical_json_matches_contract(self) -> None:
        """canonical_json() produces identical output to API contract."""
        obj = {"b": 2, "a": 1, "c": {"z": 26, "a": 1}}
        assert canonical_json(obj) == contract_canonical_json(obj)

    def test_receipt_hash_matches_contract(self) -> None:
        """compute_receipt_hash() produces identical output to API contract."""
        params = ("POST", "http://localhost/api/v1/intelligence/cii", "country=IRN",
                  "accept:application/json", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
        assert compute_receipt_hash(*params) == contract_compute_receipt_hash(*params)
