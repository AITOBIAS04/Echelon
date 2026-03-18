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
    ".download_meta.json",
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
    (
        "arxiv-ml-metadata",
        "https://info.arxiv.org/help/bulk_data.html",
        "2026-03",
        None,
    ),
]


# ── Standards Registry ─────────────────────────────────────────────

# Initial standards assets with canonical metadata.
# Each tuple: (asset_id, source_url, version, license)
STANDARDS_CATALOG: list[tuple[str, str, str, Optional[str]]] = [
    (
        "wcag",
        "https://www.w3.org/TR/WCAG22/",
        "2.2",
        None,
    ),
    (
        "aria-apg",
        "https://www.w3.org/WAI/ARIA/apg/",
        "2024",
        None,
    ),
    (
        "react-docs",
        "https://react.dev/reference",
        "2026-03",
        None,
    ),
    (
        "tailwind-docs",
        "https://tailwindcss.com/docs",
        "2026-03",
        None,
    ),
    (
        "owasp-top10",
        "https://owasp.org/www-project-top-ten/",
        "2025",
        None,
    ),
    (
        "cwe-subset",
        "https://cwe.mitre.org/top25/",
        "2026-03",
        None,
    ),
    # ── Cycle-026c: User Research + Journey Anchors ──
    (
        "user-research-methods",
        "https://www.gov.uk/service-manual/user-research",
        "2026-03",
        "OGL-3.0",
    ),
    (
        "journey-patterns",
        "https://design-system.service.gov.uk/patterns/",
        "2026-03",
        "OGL-3.0",
    ),
    (
        "recovery-guidance",
        "https://design-system.service.gov.uk/patterns/validation/",
        "2026-03",
        "OGL-3.0",
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


def r2_key_prefix(
    asset_id: str,
    version: str,
    *,
    asset_class: str = "benchmark",
) -> str:
    """Return the R2 key prefix for a given asset and version.

    Convention:
      - ``benchmarks/{asset_id}/{version}/`` for ``asset_class="benchmark"``
      - ``standards/{asset_id}/{version}/`` for ``asset_class="standard"``

    Raises:
        ValueError: If ``asset_class`` is not ``"benchmark"`` or ``"standard"``.
    """
    prefix_map = {
        "benchmark": "benchmarks",
        "standard": "standards",
    }
    bucket = prefix_map.get(asset_class)
    if bucket is None:
        raise ValueError(
            f"Unknown asset_class {asset_class!r}. "
            f"Expected one of: {sorted(prefix_map.keys())}"
        )
    return f"{bucket}/{asset_id}/{version}/"


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


# ── Standards Registry Builder ─────────────────────────────────────

def _resolve_asset_dir(staging_root: Path, asset_id: str, version: str, *, asset_class: str = "standard") -> Optional[Path]:
    """Locate a local asset directory, checking multiple layout conventions.

    Tried in order:
      1. R2-normalized: ``{class_plural}/{asset_id}/{version}/raw/``
      2. Flat staging:  ``{asset_id}/``

    Returns the first directory that exists, or ``None``.
    """
    class_plural = "standards" if asset_class == "standard" else "benchmarks"

    # R2-normalized layout
    r2_path = staging_root / class_plural / asset_id / version / "raw"
    if r2_path.is_dir():
        return r2_path

    # Flat staging layout (download scripts produce this)
    flat_path = staging_root / asset_id
    if flat_path.is_dir():
        return flat_path

    return None


def build_standards_registry(
    staging_root: Optional[Path] = None,
    *,
    registry_version: str = "1.0",
) -> DatasetRegistryDocument:
    """Build a ``DatasetRegistryDocument`` for all catalogued standards.

    Iterates over ``STANDARDS_CATALOG``, builds a manifest for each
    standard whose local directory exists under ``staging_root``, and
    wraps the results in a registry document.

    Accepted directory layouts under ``staging_root``:

    1. R2-normalized: ``standards/{asset_id}/{version}/raw/``
    2. Flat staging:  ``{asset_id}/``

    Args:
        staging_root: Base directory containing downloaded standard assets.
            Defaults to :func:`get_staging_root` if not provided.
        registry_version: Version string for the registry document.

    Returns:
        A ``DatasetRegistryDocument`` containing one entry per standard
        whose local directory is present.

    Raises:
        ValueError: If no standards could be built (no directories found).
    """
    if staging_root is None:
        staging_root = get_staging_root()

    entries: list[DatasetRegistryEntry] = []

    for asset_id, source_url, version, asset_license in STANDARDS_CATALOG:
        asset_dir = _resolve_asset_dir(staging_root, asset_id, version, asset_class="standard")
        if asset_dir is None:
            continue

        entry = build_manifest(
            asset_dir,
            asset_id=asset_id,
            asset_class="standard",
            source_url=source_url,
            version=version,
            license=asset_license,
        )
        entries.append(entry)

    if not entries:
        raise ValueError(
            "No standards could be built. Ensure at least one standard "
            "directory exists under the staging root at "
            f"standards/{{asset_id}}/{{version}}/raw/ or {{asset_id}}/."
        )

    return build_registry_document(entries, registry_version=registry_version)
