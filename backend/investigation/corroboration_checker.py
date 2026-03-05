"""Investigation Corroboration Checker — claim-centric independence enforcement."""

from __future__ import annotations

from backend.investigation.claim_graph import ClaimNode, ClaimStatus, CorroborationCheck


class InvestigationCorroborationChecker:
    """Derive claim status from corroboration checks.

    Hard invariant: SUPPORTED requires >=2 distinct upstream_group values
    with status='confirmed'. No override mechanism, no admin bypass.

    Rules:
    - >=2 distinct confirmed upstream groups → SUPPORTED
    - 1 confirmed upstream group → PARTIALLY_SUPPORTED
    - Any contradicted check → CONTRADICTED
    - Otherwise → UNCONFIRMED
    """

    def evaluate_claim(
        self,
        claim: ClaimNode,
        checks: list[CorroborationCheck],
    ) -> ClaimStatus:
        """Derive claim status from corroboration checks."""
        if not checks:
            return ClaimStatus.UNCONFIRMED

        # Check for contradictions first
        if any(c.status == "contradicted" for c in checks):
            return ClaimStatus.CONTRADICTED

        # Count distinct upstream groups with confirmed status
        independent_count = self._count_independent_groups(checks)

        if independent_count >= 2:
            return ClaimStatus.SUPPORTED
        elif independent_count == 1:
            return ClaimStatus.PARTIALLY_SUPPORTED
        else:
            return ClaimStatus.UNCONFIRMED

    def _count_independent_groups(
        self, checks: list[CorroborationCheck]
    ) -> int:
        """Count distinct upstream_group values with status='confirmed'."""
        confirmed_groups: set[str] = set()
        for check in checks:
            if check.status == "confirmed":
                confirmed_groups.add(check.upstream_group)
        return len(confirmed_groups)
