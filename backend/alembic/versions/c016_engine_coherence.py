"""016 Engine Coherence Lock — enum extension, stability normalisation, anchor fields

Revision ID: c016_engine_coherence
Revises: c014c_stop_condition
Create Date: 2026-03-05

Sprint-0 migration:
- Extend WingFlapType enum with 10 new values
- Add FlapDirection enum (STABILISE, DESTABILISE, NEUTRAL)
- Normalise stability/surface_tension/osint_alignment from 0-100 → 0-1
- Add anchor/fork fields to timelines (is_anchor, anchor_timeline_id, fork_divergence, last_sync_at)
- Add updated_at to timelines
- Add ix_timelines_anchor index
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c016_engine_coherence"
down_revision: Union[str, None] = "c014c_stop_condition"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# New WingFlapType enum values added in 016
NEW_FLAP_TYPES = [
    "MIRROR_SYNC",
    "MIRROR_TRADE",
    "EVIDENCE",
    "CLAIM",
    "COUNTER_SIGNAL",
    "CORROBORATION",
    "DETONATION",
    "FORK_SPAWN",
    "STOP_CONDITION",
    "CERTIFICATE",
]


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # --- 1. Extend WingFlapType enum (PostgreSQL ALTER TYPE ... ADD VALUE) ---
    if conn.dialect.name == "postgresql":
        # Get existing enum values to avoid duplicates
        result = conn.execute(
            sa.text("SELECT unnest(enum_range(NULL::wingflaptype))::text")
        )
        existing_values = {row[0] for row in result}

        for val in NEW_FLAP_TYPES:
            if val not in existing_values:
                conn.execute(
                    sa.text(f"ALTER TYPE wingflaptype ADD VALUE IF NOT EXISTS '{val}'")
                )

    # --- 2. Add anchor/fork columns to timelines ---
    timeline_cols = [c["name"] for c in inspector.get_columns("timelines")]

    if "is_anchor" not in timeline_cols:
        op.add_column(
            "timelines",
            sa.Column("is_anchor", sa.Boolean(), server_default="false", nullable=False),
        )
    if "anchor_timeline_id" not in timeline_cols:
        op.add_column(
            "timelines",
            sa.Column("anchor_timeline_id", sa.String(50), nullable=True),
        )
        # FK constraint
        op.create_foreign_key(
            "fk_timelines_anchor_timeline",
            "timelines",
            "timelines",
            ["anchor_timeline_id"],
            ["id"],
        )
    if "fork_divergence" not in timeline_cols:
        op.add_column(
            "timelines",
            sa.Column("fork_divergence", sa.Float(), server_default="0.0", nullable=False),
        )
    if "last_sync_at" not in timeline_cols:
        op.add_column(
            "timelines",
            sa.Column("last_sync_at", sa.DateTime(), nullable=True),
        )
    if "updated_at" not in timeline_cols:
        op.add_column(
            "timelines",
            sa.Column(
                "updated_at",
                sa.DateTime(),
                server_default=sa.text("now()"),
                nullable=True,
            ),
        )

    # --- 3. Add ix_timelines_anchor index ---
    existing_indexes = [idx["name"] for idx in inspector.get_indexes("timelines")]
    if "ix_timelines_anchor" not in existing_indexes:
        op.create_index("ix_timelines_anchor", "timelines", ["is_anchor"])

    # --- 4. Normalise stability / surface_tension / osint_alignment: 0-100 → 0-1 ---
    # Only normalise rows that look like old scale (> 1.0)
    op.execute(
        sa.text(
            "UPDATE timelines SET stability = stability / 100.0 WHERE stability > 1.0"
        )
    )
    op.execute(
        sa.text(
            "UPDATE timelines SET surface_tension = surface_tension / 100.0 WHERE surface_tension > 1.0"
        )
    )
    op.execute(
        sa.text(
            "UPDATE timelines SET osint_alignment = osint_alignment / 100.0 WHERE osint_alignment > 1.0"
        )
    )

    # Also normalise private_forks.stability
    pf_cols = [c["name"] for c in inspector.get_columns("private_forks")]
    if "stability" in pf_cols:
        op.execute(
            sa.text(
                "UPDATE private_forks SET stability = stability / 100.0 WHERE stability > 1.0"
            )
        )

    # --- 5. Direction semantics: ANCHOR -> STABILISE ---
    wing_flap_cols = [c["name"] for c in inspector.get_columns("wing_flaps")]
    if "direction" in wing_flap_cols:
        op.execute(
            sa.text(
                "UPDATE wing_flaps SET direction = 'STABILISE' WHERE direction = 'ANCHOR'"
            )
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    timeline_cols = [c["name"] for c in inspector.get_columns("timelines")]

    # --- Reverse normalisation: 0-1 → 0-100 ---
    op.execute(
        sa.text(
            "UPDATE timelines SET stability = stability * 100.0 WHERE stability <= 1.0"
        )
    )
    op.execute(
        sa.text(
            "UPDATE timelines SET surface_tension = surface_tension * 100.0 WHERE surface_tension <= 1.0"
        )
    )
    op.execute(
        sa.text(
            "UPDATE timelines SET osint_alignment = osint_alignment * 100.0 WHERE osint_alignment <= 1.0"
        )
    )

    pf_cols = [c["name"] for c in inspector.get_columns("private_forks")]
    if "stability" in pf_cols:
        op.execute(
            sa.text(
                "UPDATE private_forks SET stability = stability * 100.0 WHERE stability <= 1.0"
            )
        )

    # Reverse direction semantics for downgrade compatibility.
    wing_flap_cols = [c["name"] for c in inspector.get_columns("wing_flaps")]
    if "direction" in wing_flap_cols:
        op.execute(
            sa.text(
                "UPDATE wing_flaps SET direction = 'ANCHOR' WHERE direction = 'STABILISE'"
            )
        )

    # --- Drop anchor/fork columns ---
    existing_indexes = [idx["name"] for idx in inspector.get_indexes("timelines")]
    if "ix_timelines_anchor" in existing_indexes:
        op.drop_index("ix_timelines_anchor", table_name="timelines")

    if "updated_at" in timeline_cols:
        op.drop_column("timelines", "updated_at")
    if "last_sync_at" in timeline_cols:
        op.drop_column("timelines", "last_sync_at")
    if "fork_divergence" in timeline_cols:
        op.drop_column("timelines", "fork_divergence")
    if "anchor_timeline_id" in timeline_cols:
        op.drop_constraint("fk_timelines_anchor_timeline", "timelines", type_="foreignkey")
        op.drop_column("timelines", "anchor_timeline_id")
    if "is_anchor" in timeline_cols:
        op.drop_column("timelines", "is_anchor")

    # NOTE: PostgreSQL does not support DROP VALUE from enums.
    # New enum values remain after downgrade.
