"""Tests for security-specific anchor mapping rules.

Cycle 037c: Security + Domain Pack Verification.
"""

from backend.schemas.construct_anchor_schema import AnchorClass
from backend.services.construct_anchor_mapper import (
    _MAPPING_RULES,
    map_dimension_anchors,
)


class TestAttackFrameworkAnchor:
    def test_attack_dimension_maps_to_public_standard(self):
        """ATT&CK dimension maps to PUBLIC_STANDARD with attack_framework anchor."""
        result = map_dimension_anchors("attack_technique_mapping")

        assert result.weakly_anchored is False
        anchor_ids = {a.anchor_id for a in result.anchors}
        assert "attack_framework" in anchor_ids

        attack_anchor = next(a for a in result.anchors if a.anchor_id == "attack_framework")
        assert attack_anchor.anchor_class == AnchorClass.PUBLIC_STANDARD

    def test_mitre_dimension(self):
        """Dimension containing 'mitre' maps to attack_framework."""
        result = map_dimension_anchors("mitre_att_ck_coverage")

        anchor_ids = {a.anchor_id for a in result.anchors}
        assert "attack_framework" in anchor_ids


class TestSecuritySkillCorpusAnchor:
    def test_skill_corpus_dimension(self):
        """Dimension containing 'security_skill' maps to security_skill_corpus."""
        result = map_dimension_anchors("security_skill_verification")

        assert result.weakly_anchored is False
        anchor_ids = {a.anchor_id for a in result.anchors}
        assert "security_skill_corpus" in anchor_ids

        corpus_anchor = next(a for a in result.anchors if a.anchor_id == "security_skill_corpus")
        assert corpus_anchor.anchor_class == AnchorClass.PUBLIC_STANDARD

    def test_workflow_verification_dimension(self):
        """Dimension containing 'workflow_verification' maps to security_skill_corpus."""
        result = map_dimension_anchors("workflow_verification_check")

        anchor_ids = {a.anchor_id for a in result.anchors}
        assert "security_skill_corpus" in anchor_ids


class TestMissingAnchorWeaklyAnchored:
    def test_unrecognized_dimension(self):
        """Unrecognized security claim is weakly_anchored."""
        result = map_dimension_anchors("completely_unknown_dimension_xyz")

        assert result.weakly_anchored is True
        assert result.anchors == []


class TestOriginalRulesPreserved:
    def test_mapping_rules_count(self):
        """_MAPPING_RULES now has 13 entries (11 original + 2 new)."""
        assert len(_MAPPING_RULES) == 13

    def test_existing_security_standards_rule_intact(self):
        """The original security_standards rule (cycle-026b) is still present."""
        anchor_ids = [rule[2] for rule in _MAPPING_RULES]
        assert "security_standards" in anchor_ids

    def test_original_code_verification_rule(self):
        """The original code_verification rule is still present."""
        anchor_ids = [rule[2] for rule in _MAPPING_RULES]
        assert "code_verification" in anchor_ids
