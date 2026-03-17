"""R2 Manifest Builder — local directory to DatasetRegistryEntry.

Scans a local asset directory, computes per-file SHA-256 hashes,
and produces a DatasetRegistryEntry suitable for R2 upload.
Used by the construct evidence anchoring pipeline (Cycle-026a).

This service works on LOCAL directories only. It does not communicate
with R2 directly — the output manifest is consumed by an upload step.
"""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from backend.schemas.eval_asset_registry import (
    DatasetRegistryDocument,
    DatasetRegistryEntry,
    RegistryFileEntry,
)
from backend.services.eval_asset_policy import reject_live_as_immutable


# ── Constants ───────────────────────────────────────────────────────

# Artifacts to skip when building manifests.  These are transport/cache
# files that should never appear in an immutable R2 snapshot.
SKIP_NAMES: frozenset[str] = frozenset({
    ".cache",
    ".gitattributes",
    ".huggingface",
    "__pycache__",
})

# Chunk size for streaming SHA-256 (64 KB)
_HASH_CHUNK_SIZE = 65_536


# ── Benchmark Registry ──────────────────────────────────────────────

# Initial benchmark assets with canonical metadata.
# Each tuple: (asset_id, source_url, version, license)
BENCHMARK_CATALOG: list[tuple[str, str, str, Optional[str]]] = [
    (
        "humaneval",
        "https://github.com/openai/human-eval",
        "v1.0",
        "MIT",
    ),
    (
        "mbpp",
        "https://github.com/google-research/google-research/tree/master/mbpp",
        "v1.0",
        "Apache-2.0",
    ),
    (
        "hellaswag",
        "https://github.com/rowanz/hellaswag",
        "v1.0",
        "MIT",
    ),
    (
        "mmlu",
        "https://github.com/hendrycks/test",
        "v1.0",
        "MIT",
    ),
    (
        "mmlu-pro",
        "https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro",
        "v1.0",
        "MIT",
    ),
    (
        "swe-bench-verified",
        "https://github.com/princeton-nlp/SWE-bench",
        "v1.0",
        "MIT",
    ),
]


# ── Helpers ─────────────────────────────────────────────────────────

def sha256_file(filepath: Path) -> str:
    """Compute SHA-256 of a file, streaming in 64 KB chunks.

    Returns the hash as ``sha256:<hex>``.
    """
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(_HASH_CHUNK_SIZE)
            if not chunk:
                break
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


def sha256_json(file_entries: list[RegistryFileEntry]) -> str:
    """Compute a top-level hash from a sorted list of file entries.

    Canonical JSON of the file list (sorted by path) is hashed to
    produce a deterministic aggregate content_hash.

    Returns the hash as ``sha256:<hex>``.
    """
    sorted_entries = sorted(file_entries, key=lambda e: e.path)
    payload = [
        {"path": e.path, "size_bytes": e.size_bytes, "content_hash": e.content_hash}
        for e in sorted_entries
    ]
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    h = hashlib.sha256(canonical.encode("utf-8"))
    return f"sha256:{h.hexdigest()}"


def _should_skip(name: str) -> bool:
    """Return True if a file or directory name should be excluded."""
    return name in SKIP_NAMES


def get_staging_root() -> Path:
    """Return the local eval data staging root.

    Reads ``ECHELON_EVAL_DATA_ROOT`` from the environment, falling back
    to ``~/.echelon/eval_data`` if unset.
    """
    env_val = os.environ.get("ECHELON_EVAL_DATA_ROOT")
    if env_val:
        return Path(env_val)
    return Path.home() / ".echelon" / "eval_data"


def r2_key_prefix(asset_id: str, version: str) -> str:
    """Return the R2 key prefix for a given asset and version.

    Convention: ``benchmarks/{asset_id}/{version}/``
    """
    return f"benchmarks/{asset_id}/{version}/"


# ── Core Builder ────────────────────────────────────────────────────

def build_manifest(
    asset_root: Path,
    *,
    asset_id: str,
    asset_class: str = "benchmark",
    source_url: str,
    version: str,
    license: Optional[str] = None,
) -> DatasetRegistryEntry:
    """Build a manifest for a local asset directory.

    Walks ``asset_root`` recursively, skipping transport/cache artifacts.
    Computes per-file SHA-256 hashes and a top-level aggregate hash.

    Args:
        asset_root: Path to the local directory containing asset files.
        asset_id: Filesystem-safe asset identifier.
        asset_class: ``"benchmark"`` or ``"standard"``.
        source_url: Canonical upstream URL for the dataset.
        version: Version tag for this snapshot.
        license: Optional SPDX license identifier.

    Returns:
        A fully populated ``DatasetRegistryEntry``.

    Raises:
        ValueError: If ``asset_root`` does not exist, contains no eligible
            files, or the asset is live-only per policy.
        FileNotFoundError: If ``asset_root`` does not exist.
    """
    # Policy gate: reject live-only assets before doing any work
    reject_live_as_immutable(asset_id)

    asset_root = Path(asset_root)
    if not asset_root.is_dir():
        raise FileNotFoundError(f"Asset root does not exist: {asset_root}")

    file_entries: list[RegistryFileEntry] = []

    for dirpath, dirnames, filenames in os.walk(asset_root):
        # Prune skipped directories in-place so os.walk doesn't descend
        dirnames[:] = [d for d in dirnames if not _should_skip(d)]

        for filename in sorted(filenames):
            if _should_skip(filename):
                continue

            full_path = Path(dirpath) / filename
            rel_path = full_path.relative_to(asset_root).as_posix()
            size_bytes = full_path.stat().st_size
            content_hash = sha256_file(full_path)

            file_entries.append(
                RegistryFileEntry(
                    path=rel_path,
                    size_bytes=size_bytes,
                    content_hash=content_hash,
                )
            )

    if not file_entries:
        raise ValueError(
            f"No eligible files found in {asset_root}. "
            f"Check that the directory contains non-skipped files."
        )

    # Sort by path for deterministic ordering
    file_entries.sort(key=lambda e: e.path)

    top_hash = sha256_json(file_entries)

    return DatasetRegistryEntry(
        asset_id=asset_id,
        asset_class=asset_class,
        source_url=source_url,
        version=version,
        license=license,
        retrieved_at=datetime.now(timezone.utc),
        content_hash=top_hash,
        files=file_entries,
    )


# ── Registry Document Builder ──────────────────────────────────────

def build_registry_document(
    entries: list[DatasetRegistryEntry],
    *,
    registry_version: str = "1.0",
) -> DatasetRegistryDocument:
    """Build an aggregate registry document from individual entries.

    Args:
        entries: List of ``DatasetRegistryEntry`` objects.
        registry_version: Version string for the registry document.

    Returns:
        A ``DatasetRegistryDocument`` ready for serialization.
    """
    return DatasetRegistryDocument(
        version=registry_version,
        generated_at=datetime.now(timezone.utc),
        entries=entries,
    )
