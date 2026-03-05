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
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("theatres")]
    if "stop_condition" not in columns:
        op.add_column("theatres", sa.Column("stop_condition", sa.String(30), nullable=True))
    if "stop_config" not in columns:
        op.add_column("theatres", sa.Column("stop_config", sa.JSON(), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("theatres")]
    if "stop_config" in columns:
        op.drop_column("theatres", "stop_config")
    if "stop_condition" in columns:
        op.drop_column("theatres", "stop_condition")
