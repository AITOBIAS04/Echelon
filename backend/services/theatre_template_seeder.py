"""
Theatre Template Seeder — Seeds genesis theatre templates for the Create Theatre flow.

These are the canonical template definitions that power the
GET /api/v1/templates endpoint and the Create Theatre UI.

Idempotent: re-seeding skips existing templates (matched by primary key).
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models import TheatreTemplate

logger = logging.getLogger(__name__)

# ── Genesis Theatre Templates ──────────────────────────────────────────────
# Each template is a row in theatre_templates.  The template_json column
# carries the full schema that the Theatre engine validates on commit.

GENESIS_TEMPLATES = [
    {
        "id": "counterfactual_geopolitical_v1",
        "template_family": "counterfactual",
        "execution_path": "market",
        "display_name": "Geopolitical Counterfactual",
        "description": "Model alternative geopolitical outcomes — sanctions, regime changes, military escalations. Market-path execution with OSINT-sourced ground truth.",
        "schema_version": "2.0",
        "inquiry_class": "COUNTERFACTUAL",
        "template_json": {
            "theatre_id": "counterfactual_geopolitical_v1",
            "execution_path": "market",
            "inquiry_class": "COUNTERFACTUAL",
            "episode_count": 100,
            "ground_truth_source": "osint",
            "scoring": {"method": "brier", "calibration_bins": 10},
        },
    },
    {
        "id": "counterfactual_financial_v1",
        "template_family": "counterfactual",
        "execution_path": "market",
        "display_name": "Financial Event Counterfactual",
        "description": "Model alternative financial outcomes — rate decisions, earnings surprises, de-pegs. Market-path execution with oracle-sourced ground truth.",
        "schema_version": "2.0",
        "inquiry_class": "COUNTERFACTUAL",
        "template_json": {
            "theatre_id": "counterfactual_financial_v1",
            "execution_path": "market",
            "inquiry_class": "COUNTERFACTUAL",
            "episode_count": 100,
            "ground_truth_source": "oracle",
            "scoring": {"method": "brier", "calibration_bins": 10},
        },
    },
    {
        "id": "counterfactual_tech_v1",
        "template_family": "counterfactual",
        "execution_path": "market",
        "display_name": "Technology Counterfactual",
        "description": "Model alternative technology outcomes — acquisitions, product launches, regulatory actions. Market-path execution with mixed ground truth.",
        "schema_version": "2.0",
        "inquiry_class": "COUNTERFACTUAL",
        "template_json": {
            "theatre_id": "counterfactual_tech_v1",
            "execution_path": "market",
            "inquiry_class": "COUNTERFACTUAL",
            "episode_count": 100,
            "ground_truth_source": "mixed",
            "scoring": {"method": "brier", "calibration_bins": 10},
        },
    },
    {
        "id": "counterfactual_crypto_v1",
        "template_family": "counterfactual",
        "execution_path": "market",
        "display_name": "Crypto Event Counterfactual",
        "description": "Model alternative crypto outcomes — ETF approvals, protocol failures, stablecoin de-pegs. Market-path execution with on-chain ground truth.",
        "schema_version": "2.0",
        "inquiry_class": "COUNTERFACTUAL",
        "template_json": {
            "theatre_id": "counterfactual_crypto_v1",
            "execution_path": "market",
            "inquiry_class": "COUNTERFACTUAL",
            "episode_count": 100,
            "ground_truth_source": "onchain",
            "scoring": {"method": "brier", "calibration_bins": 10},
        },
    },
    {
        "id": "investigative_fraud_v1",
        "template_family": "investigative",
        "execution_path": "live",
        "display_name": "Financial Fraud Investigation",
        "description": "Live investigation theatre for financial fraud patterns — market manipulation, insider trading, wash trading. Stop-condition driven.",
        "schema_version": "2.0",
        "inquiry_class": "INVESTIGATIVE",
        "template_json": {
            "theatre_id": "investigative_fraud_v1",
            "execution_path": "live",
            "inquiry_class": "INVESTIGATIVE",
            "episode_count": 50,
            "ground_truth_source": "investigation",
            "scoring": {"method": "evidence_weight", "calibration_bins": 5},
        },
    },
    {
        "id": "investigative_whale_v1",
        "template_family": "investigative",
        "execution_path": "live",
        "display_name": "Whale Tracking Investigation",
        "description": "Live investigation theatre for whale wallet tracking — accumulation patterns, cross-chain movements, exchange flows.",
        "schema_version": "2.0",
        "inquiry_class": "INVESTIGATIVE",
        "template_json": {
            "theatre_id": "investigative_whale_v1",
            "execution_path": "live",
            "inquiry_class": "INVESTIGATIVE",
            "episode_count": 50,
            "ground_truth_source": "onchain",
            "scoring": {"method": "evidence_weight", "calibration_bins": 5},
        },
    },
    {
        "id": "inspection_compliance_v1",
        "template_family": "inspection",
        "execution_path": "replay",
        "display_name": "Regulatory Compliance Inspection",
        "description": "Replay-based compliance inspection — policy adherence, regulatory requirement checking, audit trail verification.",
        "schema_version": "2.0",
        "inquiry_class": "INSPECTION",
        "template_json": {
            "theatre_id": "inspection_compliance_v1",
            "execution_path": "replay",
            "inquiry_class": "INSPECTION",
            "episode_count": 25,
            "ground_truth_source": "regulatory",
            "scoring": {"method": "pass_fail", "calibration_bins": 5},
        },
    },
    {
        "id": "survey_sentiment_v1",
        "template_family": "survey",
        "execution_path": "market",
        "display_name": "Market Sentiment Survey",
        "description": "Crowd-sourced sentiment aggregation — calibrated probability estimates across agent populations.",
        "schema_version": "2.0",
        "inquiry_class": "SURVEY",
        "template_json": {
            "theatre_id": "survey_sentiment_v1",
            "execution_path": "market",
            "inquiry_class": "SURVEY",
            "episode_count": 200,
            "ground_truth_source": "aggregation",
            "scoring": {"method": "brier", "calibration_bins": 20},
        },
    },
]


def seed_theatre_templates(session: Session) -> int:
    """Seed genesis theatre templates. Idempotent — skips existing.

    Returns the number of newly created templates.
    """
    created = 0

    for tpl_data in GENESIS_TEMPLATES:
        existing = session.get(TheatreTemplate, tpl_data["id"])
        if existing:
            logger.debug("Theatre template %s already exists, skipping", tpl_data["id"])
            continue

        template = TheatreTemplate(
            id=tpl_data["id"],
            template_family=tpl_data["template_family"],
            execution_path=tpl_data["execution_path"],
            display_name=tpl_data["display_name"],
            description=tpl_data["description"],
            schema_version=tpl_data["schema_version"],
            inquiry_class=tpl_data["inquiry_class"],
            template_json=tpl_data["template_json"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(template)
        created += 1

    if created > 0:
        session.commit()
    logger.info("Seeded %d new theatre templates (total in registry: %d)", created, len(GENESIS_TEMPLATES))
    return created
