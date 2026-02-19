"""Filesystem storage layer for verification artifacts."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from echelon_verify.models import CalibrationCertificate

T = TypeVar("T", bound=BaseModel)


class Storage:
    """Simple filesystem abstraction for JSONL and JSON artifacts."""

    def __init__(self, base_dir: str = "data") -> None:
        self._base = Path(base_dir)
        self._base.mkdir(parents=True, exist_ok=True)

    @property
    def base_dir(self) -> Path:
        return self._base

    def repo_dir(self, repo: str) -> Path:
        """Get/create directory for a repository.

        Args:
            repo: Repository in ``owner/repo`` format.

        Returns:
            Path to the repo-specific data directory.
        """
        safe_name = repo.replace("/", "_")
        # Guard against path traversal
        if ".." in safe_name or safe_name.startswith("/"):
            raise ValueError(f"Invalid repo name: {repo}")
        path = self._base / safe_name
        path.mkdir(parents=True, exist_ok=True)
        return path

    def append_jsonl(self, path: Path, record: BaseModel) -> None:
        """Append a Pydantic model as one JSON line.

        Uses atomic write (write to temp, then append) to minimise
        corruption risk on partial writes.
        """
        line = record.model_dump_json() + "\n"
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write to temp file first, then append to target
        fd, tmp_path = tempfile.mkstemp(
            dir=path.parent, prefix=".tmp_", suffix=".jsonl"
        )
        try:
            os.write(fd, line.encode())
            os.close(fd)
            # Append tmp content to target
            with open(path, "a") as target:
                target.write(Path(tmp_path).read_text())
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def read_jsonl(self, path: Path, model: type[T]) -> list[T]:
        """Read all records from a JSONL file.

        Args:
            path: Path to the JSONL file.
            model: Pydantic model class to deserialize each line into.

        Returns:
            List of deserialized model instances.
        """
        if not path.exists():
            return []
        records: list[T] = []
        with open(path) as f:
            for line_num, line in enumerate(f, 1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    records.append(model.model_validate_json(stripped))
                except Exception as exc:
                    raise ValueError(
                        f"Failed to parse line {line_num} in {path}: {exc}"
                    ) from exc
        return records

    def write_certificate(self, cert: CalibrationCertificate) -> Path:
        """Write a certificate to ``certificates/{cert_id}.json``.

        Uses atomic write (temp file + rename) for safety.

        Returns:
            Path to the written certificate file.
        """
        certs_dir = self._base / "certificates"
        certs_dir.mkdir(parents=True, exist_ok=True)

        target = certs_dir / f"{cert.certificate_id}.json"

        fd, tmp_path = tempfile.mkstemp(
            dir=certs_dir, prefix=".tmp_", suffix=".json"
        )
        try:
            os.write(fd, cert.model_dump_json(indent=2).encode())
            os.close(fd)
            os.rename(tmp_path, target)
        except BaseException:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

        # Also update certificate index
        index_path = certs_dir / "index.jsonl"
        index_entry = {
            "certificate_id": cert.certificate_id,
            "construct_id": cert.construct_id,
            "composite_score": cert.composite_score,
            "replay_count": cert.replay_count,
            "timestamp": cert.timestamp.isoformat(),
        }
        with open(index_path, "a") as f:
            f.write(json.dumps(index_entry) + "\n")

        return target

    def read_certificate(self, cert_id: str) -> CalibrationCertificate:
        """Read a certificate by ID.

        Args:
            cert_id: The certificate UUID.

        Returns:
            Deserialized CalibrationCertificate.

        Raises:
            FileNotFoundError: If certificate doesn't exist.
        """
        path = self._base / "certificates" / f"{cert_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Certificate not found: {cert_id}")
        return CalibrationCertificate.model_validate_json(path.read_text())

    def list_certificates(self) -> list[dict]:
        """List certificate metadata from the index.

        Returns:
            List of certificate metadata dicts.
        """
        index_path = self._base / "certificates" / "index.jsonl"
        if not index_path.exists():
            return []
        entries: list[dict] = []
        with open(index_path) as f:
            for line in f:
                stripped = line.strip()
                if stripped:
                    entries.append(json.loads(stripped))
        return entries
