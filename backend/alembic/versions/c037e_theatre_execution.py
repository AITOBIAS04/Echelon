"""037e Theatre Execution — store construct_json on contracts for runtime execution

Revision ID: c037e_theatre_execution
Revises: c038_cross_theatre_paradox
Create Date: 2026-03-19

- Add construct_json_text column (nullable) to evaluation_contracts
  so the certificate route can load theatre fixtures at execution time.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c037e_theatre_execution"
down_revision: Union[str, None] = "c038_cross_theatre_paradox"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "evaluation_contracts",
        sa.Column("construct_json_text", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("evaluation_contracts", "construct_json_text")
