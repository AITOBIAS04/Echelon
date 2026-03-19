"""038 Cross-Theatre Paradox Detection — FactAnchors, CoherenceGroups,
CrossTheatreParadox, OracleResponse tables + WingFlapType extension

Revision ID: c038_cross_theatre_paradox
Revises: c037_evaluation_contracts
Create Date: 2026-03-19

- Create fact_anchors table
- Create fact_anchor_links table
- Create coherence_groups table
- Create coherence_group_members table
- Create cross_theatre_paradoxes table
- Create oracle_responses table
- Extend wingflaptype enum with CROSS_THEATRE_PARADOX
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c038_cross_theatre_paradox"
down_revision: Union[str, None] = "c037_evaluation_contracts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -- Extend WingFlapType enum --
    op.execute("ALTER TYPE wingflaptype ADD VALUE IF NOT EXISTS 'CROSS_THEATRE_PARADOX'")

    # -- Create CrossTheatreParadoxStatus enum --
    crosstheatreparadoxstatus = sa.Enum(
        "OPEN", "ACKNOWLEDGED", "RESOLVED", "DISMISSED",
        name="crosstheatreparadoxstatus",
    )
    crosstheatreparadoxstatus.create(op.get_bind(), checkfirst=True)

    # -- Create CrossTheatreParadoxType enum --
    crosstheatreparadoxtype = sa.Enum(
        "SETTLEMENT_DIVERGENCE", "ORACLE_INCONSISTENCY",
        "SCOPE_OVERLAP_GAP", "TEMPORAL_DRIFT",
        name="crosstheatreparadoxtype",
    )
    crosstheatreparadoxtype.create(op.get_bind(), checkfirst=True)

    # -- Create CrossTheatreParadoxSeverity enum --
    crosstheatreparadoxseverity = sa.Enum(
        "INFO", "WATCH", "MATERIAL", "CRITICAL",
        name="crosstheatreparadoxseverity",
    )
    crosstheatreparadoxseverity.create(op.get_bind(), checkfirst=True)

    # -- TABLE: fact_anchors --
    op.create_table(
        "fact_anchors",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("anchor_type", sa.String(50), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=False),
        sa.Column("external_source", sa.String(100), nullable=False),
        sa.Column("occurred_at", sa.DateTime, nullable=False),
        sa.Column("location_json", sa.JSON, nullable=True),
        sa.Column("metadata_json", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_fact_anchors_anchor_type", "fact_anchors", ["anchor_type"])
    op.create_index("ix_fact_anchors_occurred_at", "fact_anchors", ["occurred_at"])
    op.create_index(
        "ix_fact_anchors_external", "fact_anchors",
        ["external_source", "external_id"], unique=True,
    )
    op.create_index(
        "ix_fact_anchors_type_time", "fact_anchors",
        ["anchor_type", "occurred_at"],
    )

    # -- TABLE: fact_anchor_links --
    op.create_table(
        "fact_anchor_links",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("fact_anchor_id", sa.String(50), sa.ForeignKey("fact_anchors.id"), nullable=False),
        sa.Column("theatre_id", sa.String(50), sa.ForeignKey("theatres.id"), nullable=False),
        sa.Column("link_type", sa.String(30), nullable=False),
        sa.Column("link_confidence", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("linked_entity_id", sa.String(50), nullable=False),
        sa.Column("linked_entity_type", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_fact_anchor_links_fact_anchor_id", "fact_anchor_links", ["fact_anchor_id"])
    op.create_index("ix_fact_anchor_links_theatre_id", "fact_anchor_links", ["theatre_id"])
    op.create_index(
        "ix_fact_anchor_links_anchor_theatre", "fact_anchor_links",
        ["fact_anchor_id", "theatre_id"],
    )

    # -- TABLE: coherence_groups --
    op.create_table(
        "coherence_groups",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("group_type", sa.String(30), nullable=False),
        sa.Column("policy_json", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # -- TABLE: coherence_group_members --
    op.create_table(
        "coherence_group_members",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("coherence_group_id", sa.String(50), sa.ForeignKey("coherence_groups.id"), nullable=False),
        sa.Column("theatre_id", sa.String(50), sa.ForeignKey("theatres.id"), nullable=False),
        sa.Column("role", sa.String(30), nullable=False, server_default="primary"),
        sa.Column("joined_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_coherence_members_group", "coherence_group_members", ["coherence_group_id"])
    op.create_index("ix_coherence_members_theatre", "coherence_group_members", ["theatre_id"])

    # -- TABLE: cross_theatre_paradoxes --
    op.create_table(
        "cross_theatre_paradoxes",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("fact_anchor_id", sa.String(50), sa.ForeignKey("fact_anchors.id"), nullable=False),
        sa.Column("coherence_group_id", sa.String(50), sa.ForeignKey("coherence_groups.id"), nullable=True),
        sa.Column(
            "paradox_type",
            sa.Enum(
                "SETTLEMENT_DIVERGENCE", "ORACLE_INCONSISTENCY",
                "SCOPE_OVERLAP_GAP", "TEMPORAL_DRIFT",
                name="crosstheatreparadoxtype", create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "severity",
            sa.Enum(
                "INFO", "WATCH", "MATERIAL", "CRITICAL",
                name="crosstheatreparadoxseverity", create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("theatre_a_id", sa.String(50), sa.ForeignKey("theatres.id"), nullable=False),
        sa.Column("theatre_b_id", sa.String(50), sa.ForeignKey("theatres.id"), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("evidence_json", sa.JSON, nullable=False, server_default="{}"),
        sa.Column(
            "resolution_status",
            sa.Enum(
                "OPEN", "ACKNOWLEDGED", "RESOLVED", "DISMISSED",
                name="crosstheatreparadoxstatus", create_type=False,
            ),
            nullable=False,
            server_default="OPEN",
        ),
        sa.Column("resolved_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_cross_paradox_anchor", "cross_theatre_paradoxes", ["fact_anchor_id"])
    op.create_index("ix_cross_paradox_theatres", "cross_theatre_paradoxes", ["theatre_a_id", "theatre_b_id"])
    op.create_index("ix_cross_paradox_status", "cross_theatre_paradoxes", ["resolution_status"])
    op.create_index("ix_cross_paradox_severity", "cross_theatre_paradoxes", ["severity"])

    # -- TABLE: oracle_responses --
    op.create_table(
        "oracle_responses",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("theatre_id", sa.String(50), sa.ForeignKey("theatres.id"), nullable=False),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("event_id", sa.String(255), nullable=False),
        sa.Column("value_json", sa.JSON, nullable=False),
        sa.Column("queried_at", sa.DateTime, nullable=False),
        sa.Column("is_provisional", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_oracle_responses_theatre_id", "oracle_responses", ["theatre_id"])
    op.create_index("ix_oracle_responses_source", "oracle_responses", ["source"])
    op.create_index("ix_oracle_responses_source_event", "oracle_responses", ["source", "event_id"])
    op.create_index("ix_oracle_responses_theatre", "oracle_responses", ["theatre_id"])


def downgrade() -> None:
    op.drop_table("oracle_responses")
    op.drop_table("cross_theatre_paradoxes")
    op.drop_table("coherence_group_members")
    op.drop_table("coherence_groups")
    op.drop_table("fact_anchor_links")
    op.drop_table("fact_anchors")

    # Drop enums
    sa.Enum(name="crosstheatreparadoxseverity").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="crosstheatreparadoxtype").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="crosstheatreparadoxstatus").drop(op.get_bind(), checkfirst=True)

    # Note: Cannot remove a value from a PostgreSQL enum without recreating it.
    # CROSS_THEATRE_PARADOX remains in wingflaptype enum after downgrade.
