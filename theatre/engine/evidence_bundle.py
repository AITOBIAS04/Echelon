"""Evidence Bundle Builder — creates auditable evidence directory for a Theatre.

The evidence bundle contains all artefacts needed to independently reproduce
and verify a Theatre's certificate: template, commitment, ground truth,
invocations, scores, and audit trail.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from theatre.engine.canonical_json import canonical_json
from theatre.engine.commitment import CommitmentReceipt
from theatre.engine.models import AuditEvent, BundleManifest


class EvidenceBundleBuilder:
    """Builds the auditable evidence bundle directory for a Theatre."""

    REQUIRED_FILES = [
        "manifest.json",
        "template.json",
        "commitment_receipt.json",
        "scores/aggregate.json",
        "certificate.json",
    ]

    def __init__(self, theatre_id: str, output_dir: Path):
        self._theatre_id = theatre_id
        self._base_dir = output_dir / f"evidence_bundle_{theatre_id}"
        self._base_dir.mkdir(parents=True, exist_ok=True)
        (self._base_dir / "ground_truth").mkdir(exist_ok=True)
        (self._base_dir / "invocations").mkdir(exist_ok=True)
        (self._base_dir / "scores").mkdir(exist_ok=True)

    @property
    def base_dir(self) -> Path:
        return self._base_dir

    def write_manifest(self, manifest: BundleManifest) -> None:
        """Write the bundle manifest with sorted keys for determinism."""
        path = self._base_dir / "manifest.json"
        data = json.loads(manifest.model_dump_json())
        path.write_text(json.dumps(data, sort_keys=True, indent=2))

    def write_template(self, template: dict) -> None:
        """Write the committed template."""
        path = self._base_dir / "template.json"
        path.write_text(json.dumps(template, indent=2))

    def write_commitment_receipt(self, receipt: CommitmentReceipt) -> None:
        """Write the commitment receipt."""
        path = self._base_dir / "commitment_receipt.json"
        path.write_text(receipt.model_dump_json(indent=2))

    def write_ground_truth(self, dataset: list[dict], filename: str) -> None:
        """Write ground truth dataset as JSONL."""
        path = self._base_dir / "ground_truth" / filename
        with path.open("w") as f:
            for record in dataset:
                f.write(json.dumps(record, sort_keys=True) + "\n")

    def write_invocation(
        self, episode_id: str, request: dict, response: dict
    ) -> None:
        """Write a single episode invocation."""
        path = self._base_dir / "invocations" / f"{episode_id}.json"
        data = {"request": request, "response": response}
        path.write_text(json.dumps(data, indent=2))

    def write_episode_score(self, score: dict) -> None:
        """Append a per-episode score to the JSONL file."""
        path = self._base_dir / "scores" / "per_episode.jsonl"
        with path.open("a") as f:
            f.write(json.dumps(score, sort_keys=True) + "\n")

    def write_aggregate_scores(self, aggregate: dict) -> None:
        """Write aggregate scores."""
        path = self._base_dir / "scores" / "aggregate.json"
        path.write_text(json.dumps(aggregate, indent=2))

    def write_certificate(self, certificate_data: dict) -> None:
        """Write the certificate."""
        path = self._base_dir / "certificate.json"
        path.write_text(json.dumps(certificate_data, indent=2))

    def write_rlmf_export(self, records: list[dict]) -> None:
        """Write RLMF export records as JSONL."""
        path = self._base_dir / "rlmf_export.jsonl"
        with path.open("w") as f:
            for record in records:
                f.write(json.dumps(record, sort_keys=True) + "\n")

    def append_audit_event(self, event: AuditEvent) -> None:
        """Append an audit event to the trail."""
        path = self._base_dir / "audit_trail.jsonl"
        with path.open("a") as f:
            f.write(event.model_dump_json() + "\n")

    def compute_file_inventory(self) -> dict[str, str]:
        """Compute SHA-256 hashes of all files in the bundle.

        Returns dict of relative_path → SHA-256 hex, sorted lexicographically
        by key. Excludes manifest.json and certificate.json (they reference
        the inventory or are written after hash computation).
        """
        inventory: dict[str, str] = {}
        for path in sorted(self._base_dir.rglob("*")):
            if path.is_file() and path.name not in ("manifest.json", "certificate.json"):
                rel = str(path.relative_to(self._base_dir))
                inventory[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
        return dict(sorted(inventory.items()))

    def compute_bundle_hash(self) -> str:
        """Compute deterministic SHA-256 over sorted file inventory.

        Uses canonical_json for deterministic serialisation. File inventory
        keys are lexicographically sorted per hashing invariants.
        """
        inventory = self.compute_file_inventory()
        return hashlib.sha256(canonical_json(inventory).encode("utf-8")).hexdigest()

    def validate_minimum_files(self) -> list[str]:
        """Return list of missing required files. Empty = valid.

        Checks for:
        - All REQUIRED_FILES exist
        - At least 1 ground_truth file
        - At least 1 invocation file
        """
        missing: list[str] = []

        for required in self.REQUIRED_FILES:
            if not (self._base_dir / required).exists():
                missing.append(required)

        gt_dir = self._base_dir / "ground_truth"
        if not any(gt_dir.iterdir()):
            missing.append("ground_truth/ (no files)")

        inv_dir = self._base_dir / "invocations"
        if not any(inv_dir.iterdir()):
            missing.append("invocations/ (no files)")

        return missing
