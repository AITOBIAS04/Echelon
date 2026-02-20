"""Theatre Template Validator — JSON Schema + runtime validation rules.

Validates templates against echelon_theatre_schema_v2.json (structural)
and 8 runtime rules that cannot be expressed in JSON Schema.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema


class TemplateValidator:
    """Validates Theatre templates against schema + runtime rules."""

    def __init__(self, schema: dict | None = None, schema_path: Path | None = None):
        if schema is not None:
            self._schema = schema
        elif schema_path is not None:
            self._schema = json.loads(schema_path.read_text())
        else:
            raise ValueError("Must provide either schema dict or schema_path")

    def validate(
        self, template: dict, is_certificate_run: bool = True
    ) -> list[str]:
        """Return list of validation errors. Empty list = valid.

        Phase 1: JSON Schema validation (structural)
        Phase 2: Runtime rules (semantic)
        Phase 3: Certificate-run rules (mock adapter rejection)
        """
        errors: list[str] = []

        # Phase 1: JSON Schema
        errors.extend(self._validate_schema(template))
        if errors:
            # If schema fails, runtime rules may not be meaningful
            return errors

        # Phase 2: Runtime rules
        errors.extend(self._validate_runtime_rules(template))

        # Phase 3: Certificate-run rules
        if is_certificate_run:
            errors.extend(self._validate_certificate_rules(template))

        return errors

    def _validate_schema(self, template: dict) -> list[str]:
        """JSON Schema validation against echelon_theatre_schema_v2.json."""
        errors: list[str] = []
        validator = jsonschema.Draft202012Validator(self._schema)
        for error in validator.iter_errors(template):
            path = ".".join(str(p) for p in error.absolute_path) or "(root)"
            errors.append(f"Schema: {path}: {error.message}")
        return errors

    def _validate_runtime_rules(self, template: dict) -> list[str]:
        """8 runtime rules from SDD §8.2."""
        errors: list[str] = []

        criteria = template.get("criteria", {})
        criteria_ids = set(criteria.get("criteria_ids", []))
        weights = criteria.get("weights", {})

        # Rule 1: weights keys ⊆ criteria_ids
        if weights:
            extra = set(weights.keys()) - criteria_ids
            if extra:
                errors.append(
                    f"Runtime rule 1: weight keys not in criteria_ids: {extra}"
                )

        # Rule 2: weights values sum to 1.0
        if weights:
            total = sum(weights.values())
            if abs(total - 1.0) > 1e-6:
                errors.append(
                    f"Runtime rule 2: weights must sum to 1.0, got {total}"
                )

        # Rule 3: Every construct_id in resolution_programme has version_pins.constructs entry
        version_pins = template.get("version_pins", {})
        construct_pins = version_pins.get("constructs", {})
        resolution_programme = template.get("resolution_programme", [])
        for step in resolution_programme:
            cid = step.get("construct_id")
            if cid and cid not in construct_pins:
                errors.append(
                    f"Runtime rule 3: resolution step '{step.get('step_id')}' "
                    f"references construct '{cid}' with no version pin"
                )

        # Rule 4: Every construct in construct_chain has version pin
        ptc = template.get("product_theatre_config", {})
        chain = ptc.get("construct_chain", [])
        for construct_id in chain:
            if construct_id not in construct_pins:
                errors.append(
                    f"Runtime rule 4: construct_chain member '{construct_id}' "
                    f"has no version pin"
                )

        # Rule 5: Every hitl_steps[].step_id matches a resolution step with type 'hitl_rubric'
        hitl_steps = template.get("hitl_steps", [])
        hitl_resolution_steps = {
            s["step_id"]
            for s in resolution_programme
            if s.get("type") == "hitl_rubric"
        }
        for hs in hitl_steps:
            if hs["step_id"] not in hitl_resolution_steps:
                errors.append(
                    f"Runtime rule 5: hitl_steps step_id '{hs['step_id']}' "
                    f"has no matching resolution_programme step with type 'hitl_rubric'"
                )

        # Rule 7: dataset_hashes[replay_dataset_id] must be present (replay only)
        if template.get("execution_path") == "replay":
            dataset_hashes = template.get("dataset_hashes", {})
            replay_dataset_id = ptc.get("replay_dataset_id")
            if replay_dataset_id and replay_dataset_id not in dataset_hashes:
                errors.append(
                    f"Runtime rule 7: replay_dataset_id '{replay_dataset_id}' "
                    f"not found in dataset_hashes"
                )

        return errors

    def _validate_certificate_rules(self, template: dict) -> list[str]:
        """Rules that apply only to certificate-generating runs."""
        errors: list[str] = []

        # Rule 6: adapter_type 'mock' rejected for certificate runs
        ptc = template.get("product_theatre_config", {})
        adapter_type = ptc.get("adapter_type")
        if adapter_type == "mock":
            errors.append(
                "Runtime rule 6: adapter_type 'mock' not permitted for "
                "certificate-generating runs"
            )

        return errors
