#!/usr/bin/env python3
"""
End-to-end live certificate script.

Orchestrates the full OSINT pipeline against live APIs:
1. Configure theatre and collectors
2. Collect from Companies House API + London Gazette
3. Corroborate across independent sources
4. Score evidence bundles
5. Evaluate verification criteria
6. Write evidence directory
7. Build manifest and generate certificate
8. Run verifier

Usage:
    python scripts/run_live_certificate.py --company 00445790
    python scripts/run_live_certificate.py --company 00445790 --output-dir ./evidence/run_001
    python scripts/run_live_certificate.py --company 00445790 --api-key YOUR_KEY
    python scripts/run_live_certificate.py --company 00445790 --sequential
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path for imports when run as script.
_script_dir = Path(__file__).resolve().parent.parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

from osint_pipeline.collectors.companies_house import CompaniesHouseCollector
from osint_pipeline.collectors.london_gazette import LondonGazetteCollector
from osint_pipeline.engine.canonical import canonical_hash, canonical_json
from osint_pipeline.engine.certificate_generator import CertificateGenerator
from osint_pipeline.engine.corroboration import CorroborationEngine
from osint_pipeline.engine.counter_signal import CounterSignalChecker
from osint_pipeline.engine.manifest_builder import build_manifest, manifest_hash
from osint_pipeline.engine.scorer import EvidenceScorer
from osint_pipeline.models.evidence import (
    EvidenceBundle,
    GapReport,
    OracleCollectionSummary,
)
from osint_pipeline.models.oracle_output import (
    CorroborationResult,
    CounterSignalResult,
    CriterionScore,
    OracleOutput,
)
from osint_pipeline.models.registry import RegistryLoader, RegistrySource

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("live_certificate")

# Default theatre template path (relative to this script's parent).
DEFAULT_TEMPLATE = _script_dir / "theatre" / "templates" / "inspection_corporate_status_v1.json"


def load_theatre_template(template_path: Path) -> dict:
    """Load and return theatre template JSON."""
    with open(template_path, "r", encoding="utf-8") as f:
        return json.load(f)


def collect_evidence(
    company_number: str,
    api_key: str,
    sequential: bool = False,
) -> tuple[list[EvidenceBundle], list[GapReport], dict]:
    """Run Stage 1: Collection.

    Collects from:
    1. Companies House profile (first — needed for company name)
    2. Companies House filing-history
    3. London Gazette insolvency search

    Returns (bundles, gaps, company_profile_extract).
    """
    bundles: list[EvidenceBundle] = []
    gaps: list[GapReport] = []
    company_name = ""
    profile_extract: dict = {}

    # --- Step 1: Companies House profile (must be first to get company name) ---
    logger.info("Collecting: Companies House profile for %s", company_number)
    ch_collector = CompaniesHouseCollector(config={"api_key": api_key})

    try:
        profile_result = ch_collector.collect(
            query_context={"company_number": company_number},
        )
        if profile_result.succeeded:
            bundles.append(profile_result.bundle)
            profile_extract = profile_result.bundle.structured_extract
            company_name = profile_extract.get("company_name", "")
            logger.info(
                "  OK: %s — %s (%s) — confidence=%.2f",
                company_number,
                company_name,
                profile_extract.get("company_status", "unknown"),
                profile_result.bundle.confidence_score,
            )
        else:
            logger.warning("  FAIL: %s — %s", profile_result.status.value, profile_result.error_message)
            gap = ch_collector.to_gap_report(profile_result)
            gaps.append(gap)
    except Exception as e:
        logger.error("  ERROR: Companies House profile — %s", e)

    # --- Step 2: Companies House filing-history ---
    logger.info("Collecting: Companies House filing-history for %s", company_number)
    try:
        filing_result = ch_collector.collect(
            query_context={
                "company_number": company_number,
                "endpoint": "filing-history",
            },
        )
        if filing_result.succeeded:
            bundles.append(filing_result.bundle)
            logger.info(
                "  OK: %d filings — confidence=%.2f",
                filing_result.bundle.structured_extract.get("total_count", 0),
                filing_result.bundle.confidence_score,
            )
        else:
            logger.warning("  FAIL: %s — %s", filing_result.status.value, filing_result.error_message)
            gap = ch_collector.to_gap_report(filing_result)
            gaps.append(gap)
    except Exception as e:
        logger.error("  ERROR: Companies House filing-history — %s", e)

    # --- Step 3: London Gazette insolvency search ---
    search_name = company_name or f"Company {company_number}"
    logger.info("Collecting: London Gazette insolvency search for '%s'", search_name)
    lg_collector = LondonGazetteCollector()

    try:
        lg_result = lg_collector.collect(
            query_context={
                "company_name": search_name,
                "notice_type": "insolvency",
            },
        )
        if lg_result.succeeded:
            bundles.append(lg_result.bundle)
            lg_extract = lg_result.bundle.structured_extract
            logger.info(
                "  OK: %d notices — counter_signal=%s — confidence=%.2f",
                lg_extract.get("total_results", 0),
                lg_extract.get("counter_signal_detected", False),
                lg_result.bundle.confidence_score,
            )
        else:
            logger.warning("  FAIL: %s — %s", lg_result.status.value, lg_result.error_message)
            gap = lg_collector.to_gap_report(lg_result)
            gaps.append(gap)
    except Exception as e:
        logger.error("  ERROR: London Gazette — %s", e)

    # Clean up
    ch_collector.close()
    lg_collector.close()

    return bundles, gaps, profile_extract


def run_corroboration(bundles: list[EvidenceBundle]) -> list[CorroborationResult]:
    """Run Stage 2: Corroboration."""
    logger.info("Running corroboration engine...")
    engine = CorroborationEngine(
        corroboration_minimum=2,
        corroboration_window_seconds=3600,
    )

    # Build a summary for evaluate_all
    summary = OracleCollectionSummary(
        bundles=bundles,
        total_sources_attempted=len(bundles),
        total_sources_succeeded=len(bundles),
    )

    results = engine.evaluate_all(summary)
    for r in results:
        logger.info(
            "  Claim %s: %d corroborating groups (minimum=%d) — %s",
            r.claim_id,
            r.distinct_corroborating_groups,
            r.corroboration_minimum,
            "PASS" if r.passed else "FAIL",
        )

    return results


def run_counter_signal(
    bundles: list[EvidenceBundle], gaps: list[GapReport]
) -> list[CounterSignalResult]:
    """Run Stage 2b: Counter-signal checking."""
    logger.info("Running counter-signal checker...")
    checker = CounterSignalChecker()

    # Separate counter-signal bundles from primary bundles.
    # London Gazette bundles have counter_signal_class in their extract.
    cs_bundles = [
        b for b in bundles
        if b.structured_extract.get("counter_signal_class")
    ]
    # Inject counter_signal_class into query_context so the checker
    # can index bundles correctly (it reads from query_context, not extract).
    for b in cs_bundles:
        if "counter_signal_class" not in b.query_context:
            b.query_context["counter_signal_class"] = b.structured_extract.get(
                "counter_signal_class", "unknown"
            )
    cs_gaps = [
        g for g in gaps
        if g.source_group == "official_gov"  # Best approximation for LG gaps
    ]

    results = checker.evaluate(
        counter_signal_bundles=cs_bundles,
        counter_signal_gaps=cs_gaps,
        required_classes=["corporate_event"],
    )

    for r in results:
        logger.info(
            "  %s: checked=%s, signal_found=%s — %s",
            r.counter_signal_class,
            r.checked,
            r.signal_found,
            "PASS" if r.passed else "FAIL",
        )

    return results


def run_scoring(bundles: list[EvidenceBundle]) -> tuple[list[tuple[EvidenceBundle, float]], float]:
    """Run Stage 3: Scoring."""
    logger.info("Running evidence scorer...")
    scorer = EvidenceScorer()

    scored: list[tuple[EvidenceBundle, float]] = []
    for bundle in bundles:
        # Both CH and LG have immutable revision policy — no penalty.
        # We don't have registry sources loaded, so score raw bundles.
        score = scorer.score_bundle(bundle)
        scored.append((bundle, score))
        logger.info(
            "  %s: raw=%.2f, scored=%.2f",
            bundle.source_id,
            bundle.confidence_score,
            score,
        )

    composite = scorer.composite_confidence(scored)
    logger.info("  Composite confidence: %.4f", composite)

    return scored, composite


def evaluate_criteria(
    bundles: list[EvidenceBundle],
    corroboration_results: list[CorroborationResult],
    counter_signal_results: list[CounterSignalResult],
    scored_bundles: list[tuple[EvidenceBundle, float]],
) -> list[CriterionScore]:
    """Evaluate the 5 verification criteria."""
    logger.info("Evaluating verification criteria...")
    criteria: list[CriterionScore] = []

    # Find specific bundles.
    profile_bundles = [b for b in bundles if b.query_context.get("endpoint", "profile") == "profile" and "company_number" in b.query_context and "endpoint" not in b.query_context]
    # Also catch profile bundles without explicit endpoint key
    if not profile_bundles:
        profile_bundles = [b for b in bundles if b.source_id == "companies_house_api" and b.query_context.get("endpoint") is None]
    filing_bundles = [b for b in bundles if b.query_context.get("endpoint") == "filing-history"]
    lg_bundles = [b for b in bundles if b.source_id == "london_gazette_api"]

    # 1. company_exists
    profile = profile_bundles[0] if profile_bundles else None
    company_exists = profile is not None and profile.structured_extract.get("company_number") is not None
    criteria.append(CriterionScore(
        criterion_id="company_exists",
        score=1.0 if company_exists else 0.0,
        passed=company_exists,
        detail=(
            f"Company {profile.structured_extract.get('company_number')} found"
            if company_exists
            else "Company profile not retrieved"
        ),
        evidence_bundle_ids=[profile.bundle_id] if profile else [],
    ))

    # 2. company_active
    company_active = (
        profile is not None
        and profile.structured_extract.get("company_status") == "active"
    )
    criteria.append(CriterionScore(
        criterion_id="company_active",
        score=1.0 if company_active else 0.0,
        passed=company_active,
        detail=(
            f"Status: {profile.structured_extract.get('company_status')}"
            if profile
            else "No profile available"
        ),
        evidence_bundle_ids=[profile.bundle_id] if profile else [],
    ))

    # 3. filing_current
    filing = filing_bundles[0] if filing_bundles else None
    filing_current = False
    filing_detail = "No filing history available"
    if filing:
        recent_filings = filing.structured_extract.get("recent_filings", [])
        if recent_filings:
            latest_date_str = recent_filings[0].get("date", "")
            if latest_date_str:
                try:
                    latest_date = datetime.strptime(latest_date_str, "%Y-%m-%d")
                    days_ago = (datetime.now() - latest_date).days
                    filing_current = days_ago <= 365
                    filing_detail = (
                        f"Latest filing: {latest_date_str} ({days_ago} days ago)"
                    )
                except ValueError:
                    filing_detail = f"Could not parse filing date: {latest_date_str}"
    criteria.append(CriterionScore(
        criterion_id="filing_current",
        score=1.0 if filing_current else 0.0,
        passed=filing_current,
        detail=filing_detail,
        evidence_bundle_ids=[filing.bundle_id] if filing else [],
    ))

    # 4. corroboration_met
    # Use distinct independence_upstream_id count (PRD definition)
    # rather than corroboration engine's source_group count.
    upstream_ids = {b.independence_upstream_id for b in bundles}
    corroboration_met = len(upstream_ids) >= 2
    criteria.append(CriterionScore(
        criterion_id="corroboration_met",
        score=1.0 if corroboration_met else 0.0,
        passed=corroboration_met,
        detail=f"{len(upstream_ids)} distinct upstream sources (minimum 2)",
        evidence_bundle_ids=[b.bundle_id for b in bundles],
    ))

    # 5. counter_signal_absent
    counter_signal_absent = all(
        cs.passed for cs in counter_signal_results
    ) if counter_signal_results else False
    cs_detail = "No counter-signal check performed"
    if counter_signal_results:
        found = [cs for cs in counter_signal_results if cs.signal_found]
        if found:
            cs_detail = f"Counter-signal detected: {found[0].signal_detail}"
        else:
            cs_detail = "No counter-signals found (signal absence confirmed)"
    criteria.append(CriterionScore(
        criterion_id="counter_signal_absent",
        score=1.0 if counter_signal_absent else 0.0,
        passed=counter_signal_absent,
        detail=cs_detail,
        evidence_bundle_ids=[b.bundle_id for b in lg_bundles],
    ))

    for cs in criteria:
        status = "PASS" if cs.passed else "FAIL"
        logger.info("  [%s] %s: %s", status, cs.criterion_id, cs.detail)

    return criteria


def write_evidence(
    output_dir: Path,
    bundles: list[EvidenceBundle],
    gaps: list[GapReport],
    criterion_scores: list[CriterionScore],
    oracle_output: OracleOutput,
    template: dict,
) -> None:
    """Write evidence directory layout."""
    logger.info("Writing evidence to %s", output_dir)

    inputs_dir = output_dir / "inputs"
    receipts_dir = output_dir / "receipts"
    gaps_dir = output_dir / "gaps"
    scores_dir = output_dir / "scores"

    for d in [inputs_dir, receipts_dir, gaps_dir, scores_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Write inputs and receipts for each bundle.
    for bundle in bundles:
        # Determine a descriptive filename suffix.
        endpoint = bundle.query_context.get("endpoint", "profile")
        if bundle.source_id == "london_gazette_api":
            endpoint = "insolvency_search"
        elif endpoint == "profile" and "endpoint" not in bundle.query_context:
            endpoint = "profile"

        filename_base = f"{bundle.source_id}_{endpoint}"

        # Input (structured extract).
        input_path = inputs_dir / f"{filename_base}.json"
        with open(input_path, "w", encoding="utf-8") as f:
            json.dump(bundle.structured_extract, f, indent=2, default=str)

        # Receipt.
        receipt_path = receipts_dir / f"{filename_base}.receipt.json"
        with open(receipt_path, "w", encoding="utf-8") as f:
            json.dump(bundle.receipt.model_dump(mode="json"), f, indent=2)

    # Write gaps.
    for gap in gaps:
        gap_path = gaps_dir / f"{gap.source_id}.gap.json"
        with open(gap_path, "w", encoding="utf-8") as f:
            json.dump(gap.model_dump(mode="json"), f, indent=2)

    # Write criterion scores.
    scores_path = scores_dir / "criterion_scores.json"
    with open(scores_path, "w", encoding="utf-8") as f:
        json.dump(
            [cs.model_dump(mode="json") for cs in criterion_scores],
            f, indent=2,
        )

    # Write theatre template.
    template_path = output_dir / "theatre_template.json"
    with open(template_path, "w", encoding="utf-8") as f:
        json.dump(template, f, indent=2)

    # Write oracle output.
    oracle_path = output_dir / "oracle_output.json"
    with open(oracle_path, "w", encoding="utf-8") as f:
        json.dump(oracle_output.model_dump(mode="json"), f, indent=2)

    logger.info("  Evidence written: %d inputs, %d receipts, %d gaps",
                len(bundles), len(bundles), len(gaps))


def run(args: argparse.Namespace) -> int:
    """Main pipeline orchestration."""
    company_number = args.company
    api_key = args.api_key or os.environ.get("COMPANIES_HOUSE_API_KEY", "")
    output_dir = Path(args.output_dir) if args.output_dir else Path(
        f"./evidence/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    template_path = Path(args.theatre_template) if args.theatre_template else DEFAULT_TEMPLATE

    logger.info("=" * 60)
    logger.info("ECHELON LIVE CERTIFICATE PIPELINE")
    logger.info("=" * 60)
    logger.info("Company: %s", company_number)
    logger.info("Output:  %s", output_dir)
    logger.info("Template: %s", template_path)
    logger.info("")

    # --- Load theatre template ---
    template = load_theatre_template(template_path)
    commitment_hash = canonical_hash(template)
    logger.info("Theatre: %s (commitment=%s...)", template["template_id"], commitment_hash[:16])

    # --- Stage 1: Collection ---
    logger.info("")
    logger.info("STAGE 1: COLLECTION")
    logger.info("-" * 40)

    if not api_key:
        logger.error("No Companies House API key provided.")
        logger.error("Set COMPANIES_HOUSE_API_KEY env var or use --api-key")
        return 1

    bundles, gaps, profile_extract = collect_evidence(
        company_number=company_number,
        api_key=api_key,
        sequential=args.sequential,
    )

    logger.info("")
    logger.info("Collection complete: %d bundles, %d gaps", len(bundles), len(gaps))

    if not bundles:
        logger.error("No evidence collected — cannot generate certificate")
        return 1

    # --- Stage 2: Corroboration ---
    logger.info("")
    logger.info("STAGE 2: CORROBORATION")
    logger.info("-" * 40)

    corroboration_results = run_corroboration(bundles)
    counter_signal_results = run_counter_signal(bundles, gaps)

    # --- Stage 3: Scoring ---
    logger.info("")
    logger.info("STAGE 3: SCORING")
    logger.info("-" * 40)

    scored_bundles, composite_score = run_scoring(bundles)

    # --- Evaluate criteria ---
    logger.info("")
    logger.info("CRITERIA EVALUATION")
    logger.info("-" * 40)

    criterion_scores = evaluate_criteria(
        bundles=bundles,
        corroboration_results=corroboration_results,
        counter_signal_results=counter_signal_results,
        scored_bundles=scored_bundles,
    )

    # --- Assemble OracleOutput ---
    collection_summary = OracleCollectionSummary(
        bundles=bundles,
        gaps=gaps,
        total_sources_attempted=len(bundles) + len(gaps),
        total_sources_succeeded=len(bundles),
        total_sources_failed=len(gaps),
    )

    oracle_output = OracleOutput(
        oracle_id=str(uuid.uuid4()),
        theatre_id=template["template_id"],
        collection=collection_summary,
        corroboration_results=corroboration_results,
        counter_signal_results=counter_signal_results,
        criterion_scores=criterion_scores,
        composite_score=composite_score,
        bundle_hash="",  # Filled after manifest
        gap_report=gaps,
        coverage_percentage=(
            len(bundles) / max(len(bundles) + len(gaps), 1) * 100
        ),
        counter_signals_checked=sum(1 for cs in counter_signal_results if cs.checked),
        counter_signals_found=sum(1 for cs in counter_signal_results if cs.signal_found),
    )

    # --- Write evidence ---
    logger.info("")
    logger.info("WRITE EVIDENCE")
    logger.info("-" * 40)

    output_dir.mkdir(parents=True, exist_ok=True)
    write_evidence(
        output_dir=output_dir,
        bundles=bundles,
        gaps=gaps,
        criterion_scores=criterion_scores,
        oracle_output=oracle_output,
        template=template,
    )

    # --- Build manifest ---
    logger.info("")
    logger.info("BUILD MANIFEST")
    logger.info("-" * 40)

    manifest = build_manifest(output_dir)
    m_hash = manifest_hash(manifest)
    logger.info("Manifest: %d files, hash=%s...", len(manifest), m_hash[:16])

    # Write manifest.
    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # Update oracle output with bundle hash.
    oracle_output.bundle_hash = m_hash

    # --- Generate certificate ---
    logger.info("")
    logger.info("GENERATE CERTIFICATE")
    logger.info("-" * 40)

    target_entity = {
        "company_number": company_number,
        "company_name": profile_extract.get("company_name", ""),
        "company_status": profile_extract.get("company_status", ""),
    }

    generator = CertificateGenerator()
    certificate = generator.generate(
        oracle_output=oracle_output,
        manifest_hash=m_hash,
        commitment_hash=commitment_hash,
        target_entity=target_entity,
    )

    # Write certificate.
    cert_path = output_dir / "certificate.json"
    with open(cert_path, "w", encoding="utf-8") as f:
        json.dump(certificate.model_dump(mode="json"), f, indent=2)

    logger.info("Certificate: %s", certificate.certificate_id)
    logger.info("  Tier: %s", certificate.verification_tier)
    logger.info("  Score: %.4f", certificate.composite_score)
    logger.info("  All passed: %s", certificate.all_criteria_passed)

    # --- Verify ---
    logger.info("")
    logger.info("VERIFICATION")
    logger.info("-" * 40)

    from echelon_verify import verify

    success = verify(cert_path, output_dir)

    logger.info("")
    logger.info("=" * 60)
    if success:
        logger.info("PIPELINE COMPLETE: PASS")
    else:
        logger.info("PIPELINE COMPLETE: FAIL")
    logger.info("=" * 60)
    logger.info("Evidence: %s", output_dir)
    logger.info("Certificate: %s", cert_path)

    return 0 if success else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Echelon Live Certificate Pipeline",
    )
    parser.add_argument(
        "--company", required=True,
        help="Companies House company number (e.g. 00445790)",
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="Evidence output directory (default: ./evidence/{timestamp})",
    )
    parser.add_argument(
        "--api-key", default=None,
        help="Companies House API key (default: $COMPANIES_HOUSE_API_KEY)",
    )
    parser.add_argument(
        "--theatre-template", default=None,
        help="Path to theatre template JSON (default: built-in INSPECTION)",
    )
    parser.add_argument(
        "--sequential", action="store_true",
        help="Use sequential collection (for debugging)",
    )

    args = parser.parse_args()
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
