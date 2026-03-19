"""Pure-function classification adapter for orchestrated scanner handoff.

Cycle 038c: Orchestrated Scanner Handoff.

Extracts the 4 detection patterns from the real 038 CrossTheatreParadoxScanner
into pure functions that operate on ExecutedTheatreComparisonBundle pairs.
No DB, no async, no network calls.

Alignment guarantee: uses identical thresholds, severity rules, and
classification logic as the real scanner so that V2 (future DB bridge)
can replace V1 without changing classification behavior.
"""

from datetime import datetime
from typing import Optional

from backend.schemas.external_theatre_scan import (
    CandidateScanOutcome,
    ExternalTheatreScanRequest,
    ExternalTheatreScanResult,
    ParadoxFinding,
)
from backend.schemas.theatre_comparison_bundle import (
    ComparisonCandidateSet,
    ExecutedTheatreComparisonBundle,
)

# ---------------------------------------------------------------------------
# Constants — extracted from real scanner (cross_theatre_paradox_scanner.py)
# ---------------------------------------------------------------------------

ORACLE_TOLERANCE = 0.1          # 10% — from real scanner line 289
TEMPORAL_DRIFT_WINDOW = 24.0    # hours — from real scanner line 349

# Severity ordering for comparison
_SEVERITY_ORDER = {"INFO": 0, "WATCH": 1, "MATERIAL": 2, "CRITICAL": 3}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def scan_candidates(
    request: ExternalTheatreScanRequest,
) -> ExternalTheatreScanResult:
    """Classify comparison bundle pairs using all 4 detection patterns.

    Returns an ExternalTheatreScanResult with per-candidate outcomes.
    Every candidate produces either findings (paradox) or an explicit
    empty-findings result (no-paradox).
    """
    outcomes: list[CandidateScanOutcome] = []

    for candidate in request.candidates:
        bundle_a = candidate.bundle_a
        bundle_b = candidate.bundle_b

        findings: list[ParadoxFinding] = []

        f = _detect_settlement_divergence(bundle_a, bundle_b)
        if f is not None:
            findings.append(f)

        f = _detect_oracle_inconsistency(bundle_a, bundle_b)
        if f is not None:
            findings.append(f)

        f = _detect_temporal_drift(bundle_a, bundle_b)
        if f is not None:
            findings.append(f)

        f = _detect_scope_overlap_gap(bundle_a, bundle_b, candidate)
        if f is not None:
            findings.append(f)

        outcome = CandidateScanOutcome(
            construct_a_slug=bundle_a.construct_slug,
            construct_b_slug=bundle_b.construct_slug,
            candidate_type=candidate.candidate_type,
            match_strength=candidate.match_strength,
            matching_keys=candidate.matching_keys,
            findings=findings,
        )
        outcomes.append(outcome)

    total_with = sum(1 for o in outcomes if o.has_paradox)
    return ExternalTheatreScanResult(
        outcomes=outcomes,
        total_scanned=len(outcomes),
        total_with_findings=total_with,
        total_clean=len(outcomes) - total_with,
    )


# ---------------------------------------------------------------------------
# Detection Function 1: Settlement Divergence
# ---------------------------------------------------------------------------

def _detect_settlement_divergence(
    bundle_a: ExecutedTheatreComparisonBundle,
    bundle_b: ExecutedTheatreComparisonBundle,
) -> Optional[ParadoxFinding]:
    """Detect opposite settlement outcomes between two bundles.

    Severity: always MATERIAL (real scanner line 202).
    """
    state_a = bundle_a.settlement_state
    state_b = bundle_b.settlement_state

    # Insufficient data
    if state_a is None or state_b is None:
        return None
    if state_a == "PENDING" or state_b == "PENDING":
        return None

    divergent_keys: list[str] = []

    if state_a != state_b:
        # Different settlement states (e.g. SETTLED vs DISPUTED)
        pass  # Fire paradox below
    else:
        # Same state — compare outcome values on shared keys
        outcomes_a = bundle_a.settlement_outcomes
        outcomes_b = bundle_b.settlement_outcomes
        shared_keys = set(outcomes_a.keys()) & set(outcomes_b.keys())

        for key in shared_keys:
            val_a = outcomes_a[key]
            val_b = outcomes_b[key]
            # Compare resolution values if they're dicts
            if isinstance(val_a, dict) and isinstance(val_b, dict):
                res_a = val_a.get("resolution")
                res_b = val_b.get("resolution")
                if res_a is not None and res_b is not None and res_a != res_b:
                    divergent_keys.append(key)
            elif val_a != val_b:
                divergent_keys.append(key)

        if not divergent_keys and state_a == state_b:
            return None  # Same state, same outcomes — no paradox

    return ParadoxFinding(
        paradox_type="SETTLEMENT_DIVERGENCE",
        severity="MATERIAL",
        description=(
            f"Settlement divergence: {bundle_a.construct_slug} "
            f"({state_a}) vs {bundle_b.construct_slug} ({state_b})"
            + (f" — divergent keys: {divergent_keys}" if divergent_keys else "")
        ),
        evidence={
            "construct_a_settlement_state": state_a,
            "construct_b_settlement_state": state_b,
            "construct_a_outcomes": {
                k: bundle_a.settlement_outcomes.get(k)
                for k in (set(bundle_a.settlement_outcomes.keys())
                          & set(bundle_b.settlement_outcomes.keys()))
            },
            "construct_b_outcomes": {
                k: bundle_b.settlement_outcomes.get(k)
                for k in (set(bundle_a.settlement_outcomes.keys())
                          & set(bundle_b.settlement_outcomes.keys()))
            },
            "divergent_keys": divergent_keys,
        },
        construct_a_slug=bundle_a.construct_slug,
        construct_b_slug=bundle_b.construct_slug,
    )


# ---------------------------------------------------------------------------
# Detection Function 2: Oracle Inconsistency
# ---------------------------------------------------------------------------

def _detect_oracle_inconsistency(
    bundle_a: ExecutedTheatreComparisonBundle,
    bundle_b: ExecutedTheatreComparisonBundle,
) -> Optional[ParadoxFinding]:
    """Detect oracle value deltas exceeding tolerance.

    Severity: MATERIAL (same-source), WATCH (cross-source), INFO (provisional).
    Tolerance: 0.1 (10%) — real scanner line 289.
    """
    sources_a = set(bundle_a.oracle_source_ids)
    sources_b = set(bundle_b.oracle_source_ids)
    values_a = bundle_a.oracle_values
    values_b = bundle_b.oracle_values

    best_finding: Optional[ParadoxFinding] = None
    best_severity_rank = -1

    # Check shared sources first (same-source comparison)
    shared_sources = sources_a & sources_b
    for source_id in shared_sources:
        entry_a = values_a.get(source_id, {})
        entry_b = values_b.get(source_id, {})

        val_a = _extract_oracle_value(entry_a)
        val_b = _extract_oracle_value(entry_b)

        if val_a is None or val_b is None:
            continue

        # Provisional revision check
        prov_a = _extract_provisional(entry_a)
        prov_b = _extract_provisional(entry_b)
        if prov_a != prov_b:
            finding = ParadoxFinding(
                paradox_type="ORACLE_INCONSISTENCY",
                severity="INFO",
                description=(
                    f"Oracle provisional revision: source {source_id} — "
                    f"{bundle_a.construct_slug} provisional={prov_a}, "
                    f"{bundle_b.construct_slug} provisional={prov_b}"
                ),
                evidence={
                    "source_a": source_id,
                    "source_b": source_id,
                    "delta": 0.0,
                    "tolerance": ORACLE_TOLERANCE,
                    "same_source": True,
                    "value_a": val_a,
                    "value_b": val_b,
                    "is_provisional_a": prov_a,
                    "is_provisional_b": prov_b,
                },
                construct_a_slug=bundle_a.construct_slug,
                construct_b_slug=bundle_b.construct_slug,
            )
            rank = _SEVERITY_ORDER["INFO"]
            if rank > best_severity_rank:
                best_finding = finding
                best_severity_rank = rank

        # Delta check
        delta = _compute_delta(val_a, val_b)
        if delta > ORACLE_TOLERANCE:
            finding = ParadoxFinding(
                paradox_type="ORACLE_INCONSISTENCY",
                severity="MATERIAL",
                description=(
                    f"Oracle inconsistency: source {source_id} — "
                    f"delta {delta:.4f} exceeds tolerance {ORACLE_TOLERANCE}"
                ),
                evidence={
                    "source_a": source_id,
                    "source_b": source_id,
                    "delta": round(delta, 4),
                    "tolerance": ORACLE_TOLERANCE,
                    "same_source": True,
                    "value_a": val_a,
                    "value_b": val_b,
                    "is_provisional_a": prov_a,
                    "is_provisional_b": prov_b,
                },
                construct_a_slug=bundle_a.construct_slug,
                construct_b_slug=bundle_b.construct_slug,
            )
            rank = _SEVERITY_ORDER["MATERIAL"]
            if rank > best_severity_rank:
                best_finding = finding
                best_severity_rank = rank

    # Cross-source comparison if no shared sources
    if not shared_sources and values_a and values_b:
        first_source_a = next(iter(values_a))
        first_source_b = next(iter(values_b))
        val_a = _extract_oracle_value(values_a[first_source_a])
        val_b = _extract_oracle_value(values_b[first_source_b])

        if val_a is not None and val_b is not None:
            delta = _compute_delta(val_a, val_b)
            if delta > ORACLE_TOLERANCE:
                finding = ParadoxFinding(
                    paradox_type="ORACLE_INCONSISTENCY",
                    severity="WATCH",
                    description=(
                        f"Oracle cross-source inconsistency: "
                        f"{first_source_a} vs {first_source_b} — "
                        f"delta {delta:.4f} exceeds tolerance {ORACLE_TOLERANCE}"
                    ),
                    evidence={
                        "source_a": first_source_a,
                        "source_b": first_source_b,
                        "delta": round(delta, 4),
                        "tolerance": ORACLE_TOLERANCE,
                        "same_source": False,
                        "value_a": val_a,
                        "value_b": val_b,
                        "is_provisional_a": _extract_provisional(
                            values_a[first_source_a],
                        ),
                        "is_provisional_b": _extract_provisional(
                            values_b[first_source_b],
                        ),
                    },
                    construct_a_slug=bundle_a.construct_slug,
                    construct_b_slug=bundle_b.construct_slug,
                )
                rank = _SEVERITY_ORDER["WATCH"]
                if rank > best_severity_rank:
                    best_finding = finding
                    best_severity_rank = rank

    return best_finding


# ---------------------------------------------------------------------------
# Detection Function 3: Temporal Drift
# ---------------------------------------------------------------------------

def _detect_temporal_drift(
    bundle_a: ExecutedTheatreComparisonBundle,
    bundle_b: ExecutedTheatreComparisonBundle,
) -> Optional[ParadoxFinding]:
    """Detect settlement timing divergence via oracle query timestamps.

    Window: 24.0 hours (real scanner line 349).
    Severity: WATCH (>48h), INFO (24-48h).
    """
    times_a = _extract_timestamps(bundle_a)
    times_b = _extract_timestamps(bundle_b)

    if not times_a or not times_b:
        return None

    # Compute max temporal separation between the two sets
    max_delta_hours = 0.0
    best_time_a: Optional[str] = None
    best_time_b: Optional[str] = None

    for ta_str, ta_dt in times_a:
        for tb_str, tb_dt in times_b:
            delta_hours = abs((ta_dt - tb_dt).total_seconds()) / 3600.0
            if delta_hours > max_delta_hours:
                max_delta_hours = delta_hours
                best_time_a = ta_str
                best_time_b = tb_str

    if max_delta_hours <= TEMPORAL_DRIFT_WINDOW:
        return None

    if max_delta_hours > 2 * TEMPORAL_DRIFT_WINDOW:
        severity = "WATCH"
    else:
        severity = "INFO"

    return ParadoxFinding(
        paradox_type="TEMPORAL_DRIFT",
        severity=severity,
        description=(
            f"Temporal drift: {max_delta_hours:.2f}h between "
            f"{bundle_a.construct_slug} and {bundle_b.construct_slug} "
            f"(window: {TEMPORAL_DRIFT_WINDOW}h)"
        ),
        evidence={
            "delta_hours": round(max_delta_hours, 2),
            "window_hours": TEMPORAL_DRIFT_WINDOW,
            "time_a": best_time_a,
            "time_b": best_time_b,
        },
        construct_a_slug=bundle_a.construct_slug,
        construct_b_slug=bundle_b.construct_slug,
    )


# ---------------------------------------------------------------------------
# Detection Function 4: Scope Overlap Gap
# ---------------------------------------------------------------------------

def _detect_scope_overlap_gap(
    bundle_a: ExecutedTheatreComparisonBundle,
    bundle_b: ExecutedTheatreComparisonBundle,
    candidate: ComparisonCandidateSet,
) -> Optional[ParadoxFinding]:
    """Detect missing expected scope coverage.

    Only fires for overlap_scope candidates. Severity: always WATCH
    (real scanner line 428).
    """
    if candidate.candidate_type != "overlap_scope":
        return None

    scopes_a = {k.key() for k in bundle_a.scope_keys}
    scopes_b = {k.key() for k in bundle_b.scope_keys}

    missing_from_a = scopes_b - scopes_a
    missing_from_b = scopes_a - scopes_b

    if not missing_from_a and not missing_from_b:
        return None

    return ParadoxFinding(
        paradox_type="SCOPE_OVERLAP_GAP",
        severity="WATCH",
        description=(
            f"Scope overlap gap between {bundle_a.construct_slug} "
            f"and {bundle_b.construct_slug}"
        ),
        evidence={
            "construct_a_scopes": sorted(scopes_a),
            "construct_b_scopes": sorted(scopes_b),
            "missing_from_a": sorted(missing_from_a),
            "missing_from_b": sorted(missing_from_b),
            "candidate_match_strength": candidate.match_strength,
        },
        construct_a_slug=bundle_a.construct_slug,
        construct_b_slug=bundle_b.construct_slug,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_oracle_value(entry) -> Optional[float]:
    """Extract numeric oracle value from an oracle_values entry."""
    if isinstance(entry, dict):
        val = entry.get("value")
    else:
        val = entry
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _extract_provisional(entry) -> bool:
    """Extract is_provisional flag from an oracle_values entry."""
    if isinstance(entry, dict):
        return bool(entry.get("is_provisional", False))
    return False


def _compute_delta(val_a: float, val_b: float) -> float:
    """Compute absolute delta between two oracle values."""
    return abs(val_a - val_b)


def _extract_timestamps(
    bundle: ExecutedTheatreComparisonBundle,
) -> list[tuple[str, datetime]]:
    """Extract (iso_string, datetime) pairs from oracle_values queried_at."""
    results: list[tuple[str, datetime]] = []
    for entry in bundle.oracle_values.values():
        if isinstance(entry, dict):
            ts = entry.get("queried_at")
            if ts is not None and isinstance(ts, str):
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    results.append((ts, dt))
                except ValueError:
                    continue
    return results
