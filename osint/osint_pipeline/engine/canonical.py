"""
Canonical JSON and SHA-256 utilities for Echelon OSINT Pipeline.

Implements RFC 8785 (JCS) canonical JSON serialisation and SHA-256 hashing
as specified in Echelon_OSINT_Composed_Oracle_Spec_v2 §5.

Two independent fetchers querying the same endpoint with the same parameters
must produce identical receipt hashes regardless of HTTP library, header
ordering, or default user-agent strings.
"""

from __future__ import annotations

import hashlib
import json
import math
import unicodedata
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


# Headers that identify request intent, not the requester.
# Volatile headers (Authorization, X-Request-Id, Date, Cookie, etc.)
# are excluded so that two independent fetchers with different
# credentials produce identical canonical forms for the same query.
CANONICAL_HEADER_ALLOWLIST: frozenset[str] = frozenset({
    "accept",
    "content-type",
    "user-agent",
})


def _nfc_normalise_strings(obj: Any) -> Any:
    """Recursively apply Unicode NFC normalisation to all strings.

    Ensures that equivalent Unicode representations (e.g. combining
    characters vs precomposed) produce identical canonical output.
    """
    if isinstance(obj, str):
        return unicodedata.normalize("NFC", obj)
    if isinstance(obj, dict):
        return {
            unicodedata.normalize("NFC", k) if isinstance(k, str) else k: _nfc_normalise_strings(v)
            for k, v in obj.items()
        }
    if isinstance(obj, (list, tuple)):
        return [_nfc_normalise_strings(item) for item in obj]
    return obj


class _RFC8785Encoder(json.JSONEncoder):
    """Custom JSON encoder for RFC 8785 float handling.

    Uses shortest round-trip representation for floats to avoid
    platform-dependent precision artefacts (e.g. 0.1 + 0.2 producing
    0.30000000000000004 on some platforms).
    """

    def default(self, o: Any) -> Any:
        return super().default(o)

    def encode(self, o: Any) -> str:
        """Override encode to handle top-level floats."""
        return self._encode_value(o)

    def _encode_value(self, o: Any) -> str:
        if isinstance(o, float):
            return self._encode_float(o)
        if isinstance(o, bool):
            return "true" if o else "false"
        if isinstance(o, int):
            return str(o)
        if o is None:
            return "null"
        if isinstance(o, str):
            return json.dumps(o, ensure_ascii=False)
        if isinstance(o, dict):
            items = sorted(o.items(), key=lambda kv: kv[0])
            pairs = [
                f"{json.dumps(k, ensure_ascii=False)}:{self._encode_value(v)}"
                for k, v in items
            ]
            return "{" + ",".join(pairs) + "}"
        if isinstance(o, (list, tuple)):
            elements = [self._encode_value(item) for item in o]
            return "[" + ",".join(elements) + "]"
        return json.dumps(o, ensure_ascii=False)

    @staticmethod
    def _encode_float(value: float) -> str:
        """Encode float per RFC 8785: shortest round-trip representation."""
        if math.isnan(value) or math.isinf(value):
            raise ValueError(f"RFC 8785 does not permit NaN or Infinity: {value}")
        if value == 0.0:
            # Distinguish -0.0 per RFC 8785
            if math.copysign(1.0, value) < 0:
                return "-0"
            return "0"
        # Use repr for shortest round-trip, then strip
        r = repr(value)
        # Python repr may produce e.g. "0.3" which is fine
        return r


def canonical_json(obj: Any) -> str:
    """
    Produce RFC 8785 canonical JSON.

    Rules:
    - Keys sorted lexicographically
    - No whitespace between separators
    - ensure_ascii=False (UTF-8 pass-through)
    - NFC normalisation of all strings
    - Shortest round-trip float representation
    - No trailing newline
    """
    normalised = _nfc_normalise_strings(obj)
    return _RFC8785Encoder().encode(normalised)


def sha256_hex(data: str | bytes) -> str:
    """
    Compute SHA-256 hash, returned as lowercase hex (64 chars).

    Accepts str (UTF-8 encoded) or bytes.
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def canonical_hash(obj: Any) -> str:
    """
    Canonical JSON → SHA-256 in one step.

    This is the standard operation for evidence bundle hashing,
    certificate commitment hashes, and registry integrity checks.
    """
    return sha256_hex(canonical_json(obj))


def http_transcript_canonical(
    method: str,
    url: str,
    headers: dict[str, str],
    response_status: int,
    response_body: bytes,
    timestamp_ms: int,
) -> str:
    """
    Build the HTTP Transcript Canonical Form as specified in
    Composed Oracle Spec v2 §5.

    Format:
        method + "\\n"
        + canonical_url + "\\n"
        + canonical_headers + "\\n"
        + response_status + "\\n"
        + response_body_hash + "\\n"
        + timestamp_ms

    Headers are sorted by lowercase key, values trimmed, joined with ";".
    Response body hash is SHA-256 of raw bytes.
    Timestamp is UTC milliseconds (integer).
    """
    # Canonical URL: strip trailing slash, lowercase scheme+host,
    # sort query parameters by key for determinism.
    parsed = urlparse(url.rstrip("/"))
    query_params = parse_qs(parsed.query, keep_blank_values=True)
    sorted_query = urlencode(
        sorted(
            (k, v)
            for k, vs in sorted(query_params.items())
            for v in sorted(vs)
        ),
    )
    canonical_url = urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        parsed.path,
        parsed.params,
        sorted_query,
        "",  # drop fragment
    ))

    # Canonical headers: filter to allowlist, then sort by lowercase key.
    # Only intent headers (accept, content-type, user-agent) are included;
    # volatile headers (Authorization, Date, etc.) are excluded.
    sorted_headers = sorted(
        (
            (k.lower().strip(), v.strip())
            for k, v in headers.items()
            if k.lower().strip() in CANONICAL_HEADER_ALLOWLIST
        ),
        key=lambda pair: pair[0],
    )
    canonical_headers = ";".join(f"{k}={v}" for k, v in sorted_headers)

    # Response body hash
    body_hash = sha256_hex(response_body)

    # Assemble canonical form
    parts = [
        method.upper(),
        canonical_url,
        canonical_headers,
        str(response_status),
        body_hash,
        str(timestamp_ms),
    ]
    return "\n".join(parts)


def http_transcript_hash(
    method: str,
    url: str,
    headers: dict[str, str],
    response_status: int,
    response_body: bytes,
    timestamp_ms: int,
) -> str:
    """
    Compute SHA-256 of the HTTP Transcript Canonical Form.

    This is the receipt hash stored in evidence bundles.
    Two independent fetchers with identical inputs MUST produce
    identical receipt hashes.
    """
    canonical = http_transcript_canonical(
        method=method,
        url=url,
        headers=headers,
        response_status=response_status,
        response_body=response_body,
        timestamp_ms=timestamp_ms,
    )
    return sha256_hex(canonical)
