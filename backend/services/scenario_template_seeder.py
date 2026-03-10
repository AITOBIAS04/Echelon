"""
Scenario Template Seeder — Seeds 18 templates from the Echelon Scenario Packs Library v1.

4 templates with JSON fixtures become RUNNABLE (structured checkpoint graphs).
14 templates without fixtures become CATALOG_ONLY (browseable, not yet launchable).

Idempotent: re-seeding skips existing templates.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models import (
    ScenarioPackTemplate,
    ScenarioCheckpoint,
    CheckpointBranch,
)

logger = logging.getLogger(__name__)

# ── Template Family Registry ──

TEMPLATE_FAMILIES = {
    "NAV_UNC": ["neon_courier", "midnight_exchange", "runway_intercept", "last_mile_hospital"],
    "SOC_NAV": ["velvet_rope"],
    "MAN_FORCE": ["skybridge_assembly", "high_rise_steel"],
    "MARL_C3": ["disaster_response", "cooling_plant", "reactor_protocol", "heist_echelon", "blacksite_heist"],
    "3D_INERT": ["orbital_salvage", "orbital_docking"],
    "LONG_HZN": ["icebreaker_convoy"],
    "PUZ_LOGIC": ["escape_room"],
    "ADV_AIR": ["dogfight_echelon"],
    "PREC_MAN": ["cleanroom_microsurgery"],
}

# Map template_id → JSON fixture filename
FIXTURE_MAP = {
    "neon_courier": "NEON_COURIER_V1.json",
    "disaster_response": "DISASTER_RESPONSE_V1.json",
    "orbital_salvage": "ORBITAL_SALVAGE_V1.json",
    "blacksite_heist": "BLACKSITE_HEIST_V1.json",
}

# Human-readable names
TEMPLATE_NAMES = {
    "neon_courier": "Neon Courier",
    "midnight_exchange": "Midnight Exchange",
    "runway_intercept": "Runway Intercept",
    "last_mile_hospital": "Last Mile Hospital",
    "velvet_rope": "Velvet Rope",
    "skybridge_assembly": "Skybridge Assembly",
    "high_rise_steel": "High-Rise Steel",
    "disaster_response": "Disaster Response",
    "cooling_plant": "Cooling Plant",
    "reactor_protocol": "Reactor Protocol",
    "heist_echelon": "Heist Echelon",
    "blacksite_heist": "Blacksite Heist",
    "orbital_salvage": "Orbital Salvage",
    "orbital_docking": "Orbital Docking Court",
    "icebreaker_convoy": "Icebreaker Convoy",
    "escape_room": "Escape Room",
    "dogfight_echelon": "Dogfight Echelon",
    "cleanroom_microsurgery": "Cleanroom Microsurgery",
}

# Prose descriptions for catalog-only templates
TEMPLATE_DESCRIPTIONS = {
    "neon_courier": "Navigate through a neon-lit cityscape delivering high-value packages under time pressure.",
    "midnight_exchange": "Covert handoff operations in hostile territory with shifting extraction windows.",
    "runway_intercept": "Intercept and redirect cargo on active runways with narrow timing margins.",
    "last_mile_hospital": "Emergency medical supply delivery through congested urban corridors.",
    "velvet_rope": "Navigate complex social hierarchies and gatekeepers to achieve access objectives.",
    "skybridge_assembly": "Coordinate multi-crane operations to assemble skybridge segments at height.",
    "high_rise_steel": "Precision steel beam placement on active construction sites with wind interference.",
    "disaster_response": "Multi-agency crisis management with resource allocation under cascading failures.",
    "cooling_plant": "Manage thermal regulation systems under escalating failure conditions.",
    "reactor_protocol": "Nuclear facility incident response with containment and evacuation protocols.",
    "heist_echelon": "Multi-team coordinated infiltration with parallel objective execution.",
    "blacksite_heist": "Covert intelligence extraction from secured facilities under surveillance.",
    "orbital_salvage": "Recover valuable components from decommissioned spacecraft in orbital debris fields.",
    "orbital_docking": "Precision orbital docking maneuvers with tumbling target objects.",
    "icebreaker_convoy": "Long-horizon convoy navigation through Arctic ice with weather forecasting.",
    "escape_room": "Sequential puzzle solving under time pressure with branching solution paths.",
    "dogfight_echelon": "Adversarial air combat with energy management and tactical positioning.",
    "cleanroom_microsurgery": "Precision manipulation tasks in controlled environments with contamination risk.",
}

# Prose-based fork points for catalog-only templates (minimal checkpoint stubs)
CATALOG_FORK_POINTS = {
    "midnight_exchange": [
        ("rendezvous_approach", "Will the agent approach from the primary or secondary route?", ["Primary Route", "Secondary Route"]),
        ("handoff_timing", "Will the agent initiate the handoff during the first window?", ["First Window", "Wait"]),
    ],
    "runway_intercept": [
        ("intercept_angle", "Will the agent use a direct or flanking intercept approach?", ["Direct", "Flanking"]),
        ("cargo_redirect", "Will the agent redirect cargo to primary or backup facility?", ["Primary", "Backup"]),
    ],
    "last_mile_hospital": [
        ("route_selection", "Will the agent take the main road or emergency corridor?", ["Main Road", "Emergency Corridor"]),
        ("triage_priority", "Will the agent prioritize critical or stable patients first?", ["Critical First", "Stable First"]),
    ],
    "velvet_rope": [
        ("approach_strategy", "Will the agent use direct credentials or social engineering?", ["Direct Credentials", "Social Engineering"]),
        ("escalation_path", "Will the agent escalate through formal or informal channels?", ["Formal", "Informal"]),
    ],
    "skybridge_assembly": [
        ("crane_sequence", "Will the agent use sequential or parallel crane operations?", ["Sequential", "Parallel"]),
        ("wind_response", "Will the agent pause operations or adjust for wind?", ["Pause", "Adjust"]),
    ],
    "high_rise_steel": [
        ("beam_approach", "Will the agent place the beam from the north or south crane?", ["North Crane", "South Crane"]),
        ("stability_check", "Will the agent perform extended stability verification?", ["Extended Check", "Standard Check"]),
    ],
    "cooling_plant": [
        ("coolant_routing", "Will the agent route coolant through primary or backup circuit?", ["Primary Circuit", "Backup Circuit"]),
        ("emergency_shutdown", "Will the agent initiate emergency shutdown protocols?", ["Initiate Shutdown", "Continue Operating"]),
    ],
    "reactor_protocol": [
        ("containment_strategy", "Will the agent prioritize containment or evacuation?", ["Containment First", "Evacuation First"]),
        ("rod_insertion", "Will the agent use manual or automated rod insertion?", ["Manual", "Automated"]),
    ],
    "heist_echelon": [
        ("entry_point", "Will the team enter through the roof or ground level?", ["Roof Entry", "Ground Level"]),
        ("extraction_route", "Will the team use the planned or improvised extraction?", ["Planned Route", "Improvised"]),
    ],
    "orbital_docking": [
        ("approach_vector", "Will the agent use a direct or spiral approach trajectory?", ["Direct", "Spiral"]),
        ("grapple_timing", "Will the agent grapple during the current rotation window?", ["Current Window", "Wait for Next"]),
    ],
    "icebreaker_convoy": [
        ("route_planning", "Will the convoy follow the charted route or deviate for thinner ice?", ["Charted Route", "Deviate"]),
        ("weather_response", "Will the convoy shelter or push through the storm?", ["Shelter", "Push Through"]),
    ],
    "escape_room": [
        ("puzzle_sequence", "Will the agent attempt the cipher or mechanical puzzle first?", ["Cipher First", "Mechanical First"]),
        ("key_usage", "Will the agent use the found key now or save it?", ["Use Now", "Save"]),
    ],
    "dogfight_echelon": [
        ("engagement_strategy", "Will the agent engage head-on or seek altitude advantage?", ["Head-On", "Altitude Advantage"]),
        ("energy_management", "Will the agent trade speed for position?", ["Trade Speed", "Maintain Speed"]),
    ],
    "cleanroom_microsurgery": [
        ("instrument_selection", "Will the agent use the precision laser or micro-forceps?", ["Precision Laser", "Micro-Forceps"]),
        ("contamination_response", "Will the agent abort or decontaminate and continue?", ["Abort", "Decontaminate"]),
    ],
}


def _load_fixture(template_id: str) -> Optional[dict]:
    """Load JSON fixture for a template if it exists."""
    filename = FIXTURE_MAP.get(template_id)
    if not filename:
        return None

    # Try data/theatres/ first, then frontend/public/theatres/
    for base_dir in ["data/theatres", "frontend/public/theatres"]:
        path = Path(base_dir) / filename
        if path.exists():
            with open(path) as f:
                return json.load(f)
    return None


def _create_checkpoints_from_fixture(
    session: Session,
    template_id: str,
    fork_points: list[dict],
) -> int:
    """Create ScenarioCheckpoint + CheckpointBranch records from JSON fixture fork points."""
    count = 0
    for seq, fp in enumerate(fork_points, start=1):
        checkpoint = ScenarioCheckpoint(
            id=f"{template_id}_cp_{seq}",
            template_id=template_id,
            sequence_num=seq,
            trigger=fp.get("trigger", f"checkpoint_{seq}"),
            market_question=fp.get("marketQuestion", ""),
            decision_window_sec=fp.get("decisionWindowSec", 30),
            can_spawn_theatre=False,
            evaluator_type="BINARY_RISK_GATE",
            created_at=datetime.utcnow(),
        )
        session.add(checkpoint)

        for opt_idx, option in enumerate(fp.get("options", [])):
            branch = CheckpointBranch(
                id=f"{template_id}_cp_{seq}_br_{opt_idx}",
                checkpoint_id=checkpoint.id,
                label=option,
                outcome_type="continue",
            )
            session.add(branch)
        count += 1
    return count


def _create_checkpoints_from_prose(
    session: Session,
    template_id: str,
) -> int:
    """Create minimal checkpoint stubs from prose-based fork point descriptions."""
    fork_points = CATALOG_FORK_POINTS.get(template_id, [])
    count = 0
    for seq, (trigger, question, options) in enumerate(fork_points, start=1):
        checkpoint = ScenarioCheckpoint(
            id=f"{template_id}_cp_{seq}",
            template_id=template_id,
            sequence_num=seq,
            trigger=trigger,
            market_question=question,
            decision_window_sec=30,
            can_spawn_theatre=False,
            evaluator_type="BINARY_RISK_GATE",
            created_at=datetime.utcnow(),
        )
        session.add(checkpoint)

        for opt_idx, option in enumerate(options):
            branch = CheckpointBranch(
                id=f"{template_id}_cp_{seq}_br_{opt_idx}",
                checkpoint_id=checkpoint.id,
                label=option,
                outcome_type="continue",
            )
            session.add(branch)
        count += 1
    return count


def seed_templates(session: Session) -> int:
    """Seed all 18 scenario pack templates. Idempotent — skips existing.

    Returns the number of newly created templates.
    """
    created = 0

    for family, template_ids in TEMPLATE_FAMILIES.items():
        for template_id in template_ids:
            # Check if already exists
            existing = session.get(ScenarioPackTemplate, template_id)
            if existing:
                logger.debug("Template %s already exists, skipping", template_id)
                continue

            fixture = _load_fixture(template_id)
            has_fixture = fixture is not None

            # Build template record
            template = ScenarioPackTemplate(
                id=template_id,
                name=TEMPLATE_NAMES[template_id],
                description=TEMPLATE_DESCRIPTIONS.get(template_id),
                family=family,
                template_status="RUNNABLE" if has_fixture else "CATALOG_ONLY",
                is_seeded=True,
                created_at=datetime.utcnow(),
            )

            # Populate from fixture if available
            if fixture:
                meta = fixture.get("meta", {})
                template.episode_length_sec = meta.get("episodeLengthSec")
                fork_range = meta.get("forkPointsPerRunRange", [1, 10])
                template.fork_points_min = fork_range[0] if len(fork_range) > 0 else 1
                template.fork_points_max = fork_range[1] if len(fork_range) > 1 else 10
                template.settlement_latency_sec = meta.get("settlementLatencySec")

                template.objective_vector_json = fixture.get("objectiveVector")
                template.fork_point_schema_json = fixture.get("forkPointSchema")
                template.saboteur_deck_json = fixture.get("saboteurDeck")
                template.telemetry_spec_json = fixture.get("telemetrySpec")
                template.settlement_rules_json = fixture.get("settlementRules")

            session.add(template)
            session.flush()  # Ensure PK is available for FK references

            # Create checkpoint records
            if has_fixture and fixture.get("forkPointSchema"):
                cp_count = _create_checkpoints_from_fixture(
                    session, template_id, fixture["forkPointSchema"]
                )
                logger.info("Template %s: %d checkpoints from fixture", template_id, cp_count)
            else:
                cp_count = _create_checkpoints_from_prose(session, template_id)
                logger.info("Template %s: %d checkpoints from prose", template_id, cp_count)

            created += 1

    session.commit()
    logger.info("Seeded %d new templates (total in registry: 18)", created)
    return created
