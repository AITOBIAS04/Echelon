"""Test Prompt Registry — committed, hashed test prompt sets for construct verification.

Serves read-only prompt sets from JSON files in backend/data/construct_test_prompts/.
Each prompt set is hashed on load for integrity verification.
"""

import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class TestPrompt:
    """A single committed test prompt."""
    index: int
    skill_command: str
    domain: str
    prompt_text: str
    expected_criteria: list[str]
    expected_behavior: Optional[str] = None


@dataclass
class PromptSet:
    """A versioned set of committed test prompts for a construct."""
    construct_slug: str
    construct_version: str
    prompts: list[TestPrompt]
    prompts_hash: str = ""

    @property
    def count(self) -> int:
        return len(self.prompts)

    @property
    def domains(self) -> list[str]:
        return sorted(set(p.domain for p in self.prompts))

    @property
    def skills(self) -> list[str]:
        return sorted(set(p.skill_command for p in self.prompts))


def _compute_prompts_hash(prompts_data: list[dict]) -> str:
    """Compute SHA-256 hash of the prompts array (deterministic)."""
    canonical = json.dumps(prompts_data, sort_keys=True, separators=(",", ":"))
    return f"sha256:{hashlib.sha256(canonical.encode()).hexdigest()}"


class TestPromptRegistry:
    """Registry of committed test prompt sets for construct verification.

    Loads from JSON files on initialization. Read-only after load.
    """

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            data_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "data", "construct_test_prompts",
            )
        self._data_dir = data_dir
        self._sets: dict[str, PromptSet] = {}
        self._load_all()

    def _load_all(self) -> None:
        """Load all prompt set JSON files from the data directory."""
        if not os.path.isdir(self._data_dir):
            return

        for filename in os.listdir(self._data_dir):
            if not filename.endswith(".json"):
                continue
            filepath = os.path.join(self._data_dir, filename)
            with open(filepath, "r") as f:
                data = json.load(f)

            slug = data["construct_slug"]
            version = data["construct_version"]
            prompts_data = data["prompts"]
            prompts_hash = _compute_prompts_hash(prompts_data)

            prompts = [
                TestPrompt(
                    index=p["index"],
                    skill_command=p["skill_command"],
                    domain=p["domain"],
                    prompt_text=p["prompt_text"],
                    expected_criteria=p["expected_criteria"],
                    expected_behavior=p.get("expected_behavior"),
                )
                for p in prompts_data
            ]

            key = f"{slug}:{version}"
            self._sets[key] = PromptSet(
                construct_slug=slug,
                construct_version=version,
                prompts=prompts,
                prompts_hash=prompts_hash,
            )

    def get_prompts(self, slug: str, version: str) -> Optional[PromptSet]:
        """Get the prompt set for a construct version."""
        return self._sets.get(f"{slug}:{version}")

    def verify_hash(self, slug: str, version: str, expected_hash: str) -> bool:
        """Verify that a prompt set matches the expected hash."""
        prompt_set = self.get_prompts(slug, version)
        if prompt_set is None:
            return False
        return prompt_set.prompts_hash == expected_hash

    def get_prompt_at_index(self, slug: str, version: str, index: int) -> Optional[TestPrompt]:
        """Get a specific prompt by index within a prompt set."""
        prompt_set = self.get_prompts(slug, version)
        if prompt_set is None:
            return None
        for p in prompt_set.prompts:
            if p.index == index:
                return p
        return None

    def list_constructs(self) -> list[str]:
        """List all registered construct:version keys."""
        return sorted(self._sets.keys())
