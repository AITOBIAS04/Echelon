"""Construct Evidence Bundle Builder — evidence manifest and bundle hash.

Reads construct_meta_json from evidence items to produce a manifest
with per-invocation entries. Computes deterministic bundle hash.
"""

import hashlib
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ConstructEvidenceBundleBuilder:
    """Builds evidence manifests and computes bundle hashes for construct verification."""

    def build_manifest(self, evidence_items: list) -> list[dict[str, Any]]:
        """Build manifest from evidence items' construct_meta_json.

        Each entry: {prompt_index, skill_command, domain, output_hash, scores, timing_ms}
        """
        manifest = []
        for item in evidence_items:
            meta = getattr(item, "construct_meta_json", None) or {}
            entry = {
                "prompt_index": meta.get("prompt_index"),
                "skill_command": meta.get("skill_command", ""),
                "domain": meta.get("domain", ""),
                "output_hash": meta.get("output_hash", ""),
                "scores": meta.get("scores", {}),
                "timing_ms": meta.get("timing_ms", 0),
            }
            manifest.append(entry)

        # Sort by prompt_index for determinism
        manifest.sort(key=lambda e: e.get("prompt_index") or 0)
        return manifest

    def compute_bundle_hash(self, manifest: list[dict]) -> str:
        """Compute SHA-256 hash of the serialized manifest."""
        canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
        return f"sha256:{hashlib.sha256(canonical.encode()).hexdigest()}"
