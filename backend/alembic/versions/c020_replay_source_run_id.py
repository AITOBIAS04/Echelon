"""020 Add source_run_id to scenario_runs for REPLAY mode

Revision ID: c020_replay_source_run_id
Revises: c018_scenario_packs
Create Date: 2026-03-07

Adds source_run_id FK column to scenario_runs table. Nullable — only
populated for REPLAY mode runs. Self-referential FK to scenario_runs.id.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c020_replay_source_run_id"
down_revision: Union[str, None] = "c018_scenario_packs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    existing_cols = [c["name"] for c in inspector.get_columns("scenario_runs")]
    if "source_run_id" not in existing_cols:
        op.add_column(
            "scenario_runs",
            sa.Column(
                "source_run_id",
                sa.String(50),
                sa.ForeignKey("scenario_runs.id"),
                nullable=True,
                comment="For REPLAY mode: the source run whose recorded path is replayed",
            ),
        )


def downgrade() -> None:
    op.drop_column("scenario_runs", "source_run_id")
