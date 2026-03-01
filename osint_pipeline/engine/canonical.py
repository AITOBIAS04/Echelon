"""Canonical JSON and SHA-256 utilities for Echelon OSINT Pipeline.

Delegates RFC 8785 canonical JSON to ``theatre.engine.canonical_json``
(single source of truth — handles float normalisation, NaN/Infinity
rejection, bool/int distinction).

HTTP Transcript Canonical Form (6-field) per Composed Oracle Spec v2 section 5:
two independent fetchers querying the same endpoint with the same parameters
must produce identical receipt hashes regardless of HTTP library, header
ordering, or default user-agent strings.
"""

from __future__ import annotations

import hashlib
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

# K-3 fix: delegate to theatre engine (RFC 8785 with float normalisation)
# instead of skeleton's bare json.dumps.
from theatre.engine.canonical_json import canonical_json  # noqa: F401  — re-export


# Headers that identify request intent, not the requester.
# Volatile headers (Authorization, X-Request-Id, Date, Cookie, etc.)
# are excluded so that two independent fetchers with different
# credentials produce identical canonical forms for the same query.
CANONICAL_HEADER_ALLOWLIST: frozenset[str] = frozenset({
    "accept",
    "content-type",
    "user-agent",
})


def sha256_hex(data: str | bytes) -> str:
    """Compute SHA-256 hash, returned as lowercase hex (64 chars).

    Accepts str (UTF-8 encoded) or bytes.
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def canonical_hash(obj: Any) -> str:
    """Canonical JSON -> SHA-256 in one step.

    Standard operation for evidence bundle hashing, certificate
    commitment hashes, and registry integrity checks.
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
    """Build the HTTP Transcript Canonical Form (6-field).

    Format::

        METHOD\\n
        canonical_url\\n
        canonical_headers\\n
        response_status\\n
        response_body_hash\\n
        timestamp_ms

    Headers are filtered to the allowlist, sorted by lowercase key,
    values trimmed, joined with ";".
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

    # Canonical headers: filter to allowlist, sort by lowercase key.
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
    """Compute SHA-256 of the HTTP Transcript Canonical Form.

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
