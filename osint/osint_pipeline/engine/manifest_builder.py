"""
Evidence manifest builder — deterministic file inventory with SHA-256 hashes.

Produces a flat { "relative/path": "sha256_hex" } manifest from an
evidence directory. Two independent runs against identical file contents
produce identical manifest hashes.

Determinism guarantees:
- Paths use forward slashes (POSIX-normalised)
- Paths sorted lexicographically
- No timestamps in manifest
- Canonical JSON (RFC 8785) serialisation
- manifest.json and certificate.json excluded (self-referential)
"""

from __future__ import annotations

from pathlib import Path

from osint_pipeline.engine.canonical import canonical_hash, sha256_hex

# Files excluded from the manifest (self-referential or output artefacts).
MANIFEST_EXCLUDES: frozenset[str] = frozenset({
    "manifest.json",
    "certificate.json",
})


def build_manifest(evidence_dir: Path) -> dict[str, str]:
    """Build flat { "relative/path": "sha256_hex" } manifest.

    Args:
        evidence_dir: Root directory containing evidence files.

    Returns:
        Sorted dict mapping POSIX-normalised relative paths to SHA-256 hashes.
    """
    manifest: dict[str, str] = {}

    for file_path in sorted(evidence_dir.rglob("*")):
        if not file_path.is_file():
            continue

        relative = file_path.relative_to(evidence_dir)
        posix_path = relative.as_posix()

        if posix_path in MANIFEST_EXCLUDES:
            continue

        file_bytes = file_path.read_bytes()
        manifest[posix_path] = sha256_hex(file_bytes)

    return dict(sorted(manifest.items()))


def manifest_hash(manifest: dict[str, str]) -> str:
    """SHA-256 of canonical JSON of the manifest.

    This is the value stored in the certificate's evidence_bundle_hash field.
    """
    return canonical_hash(manifest)
