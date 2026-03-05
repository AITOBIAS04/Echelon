"""add stop_condition, stop_config to theatres

Revision ID: c014c_stop_condition
Revises: c014_inquiry_class
Create Date: 2026-03-05

Cycle-014c Sprint 3 — stop_condition (String) and stop_config (JSON)
columns on theatres table for investigation-class stop conditions.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c014c_stop_condition"
down_revision: Union[str, None] = "c014_inquiry_class"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    try:
        op.add_column(
            "theatres",
            sa.Column("stop_condition", sa.String(30), nullable=True),
        )
    except Exception:
        pass  # Column may already exist

    try:
        op.add_column(
            "theatres",
            sa.Column("stop_config", sa.JSON(), nullable=True),
        )
    except Exception:
        pass  # Column may already exist


def downgrade() -> None:
    try:
        op.drop_column("theatres", "stop_config")
    except Exception:
        pass

    try:
        op.drop_column("theatres", "stop_condition")
    except Exception:
        pass
