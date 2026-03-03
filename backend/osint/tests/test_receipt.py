"""HTTP transcript receipt tests — hash verification, canonical form.

Tests verify receipt hash determinism, content hash verification
against raw bytes, and the distinction between bytes-based and
dict-based content hashing.
"""
from __future__ import annotations

from backend.osint.canonical import compute_content_hash, compute_receipt_hash


class TestReceiptHashDeterminism:
    """Receipt hash computation follows the canonical spec."""

    def test_receipt_hash_deterministic(self) -> None:
        """Same HTTP transcript parameters produce same hash."""
        h1 = compute_receipt_hash(
            method="POST",
            url="http://localhost:8080/api/v1/intelligence/cii",
            query='{"country_code":"IRN"}',
            headers="content-type:application/json",
            body_hash="a" * 64,
        )
        h2 = compute_receipt_hash(
            method="POST",
            url="http://localhost:8080/api/v1/intelligence/cii",
            query='{"country_code":"IRN"}',
            headers="content-type:application/json",
            body_hash="a" * 64,
        )
        assert h1 == h2
        assert len(h1) == 64

    def test_receipt_hash_different_inputs(self) -> None:
        """Different parameters produce different hash."""
        h1 = compute_receipt_hash("POST", "http://a.com/cii", "", "", "a" * 64)
        h2 = compute_receipt_hash("POST", "http://a.com/market", "", "", "a" * 64)
        assert h1 != h2

    def test_receipt_canonical_form(self) -> None:
        """Receipt hash uses canonical HTTP transcript format:
        METHOD\\nURL\\nQUERY\\nHEADERS\\nBODY_HASH
        """
        import hashlib

        method = "POST"
        url = "http://localhost/api/v1/intelligence/cii"
        query = "country=IRN"
        headers = "accept:application/json"
        body_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

        # Manually compute expected hash
        transcript = f"{method}\n{url}\n{query}\n{headers}\n{body_hash}"
        expected = hashlib.sha256(transcript.encode("utf-8")).hexdigest()

        # Compare with function output
        actual = compute_receipt_hash(method, url, query, headers, body_hash)
        assert actual == expected


class TestContentHashMatchesRawBytes:
    """Content hash verification against raw response bytes."""

    def test_content_hash_matches_raw_bytes(self) -> None:
        """compute_content_hash(raw_bytes) produces correct SHA-256."""
        import hashlib

        raw = b'{"domain":"intelligence","bundle":{"bundle_id":"eb_test"}}'
        expected = hashlib.sha256(raw).hexdigest()
        actual = compute_content_hash(raw)
        assert actual == expected

    def test_content_hash_bytes_vs_dict_distinction(self) -> None:
        """Bytes-based hash differs from dict-based API contract hash.

        This is intentional — the pipeline hashes exact wire bytes,
        not re-serialised JSON from the dict.
        """
        from backend.schemas.worldmonitor_api_contract import (
            compute_content_hash as contract_hash,
        )
        # A dict and its JSON bytes (with spaces) will hash differently
        payload_dict = {"key": "value", "num": 42}
        raw_bytes = b'{"key": "value", "num": 42}'  # Note: spaces in JSON

        dict_hash = contract_hash(payload_dict)
        bytes_hash = compute_content_hash(raw_bytes)

        # They differ because canonical_json removes spaces
        assert dict_hash != bytes_hash
