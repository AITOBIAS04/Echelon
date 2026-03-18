"""037 Evaluation Contracts — contract-backed verification infrastructure

Revision ID: c037_evaluation_contracts
Revises: c025_osint_signals
Create Date: 2026-03-18

- Create evaluation_contracts table with partial unique index
- Add contract_hash column (nullable) to investigations
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c037_evaluation_contracts"
down_revision: Union[str, None] = "c025_osint_signals"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -- NEW TABLE: evaluation_contracts --
    op.create_table(
        "evaluation_contracts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "construct_registration_id",
            sa.String(50),
            sa.ForeignKey("construct_registrations.id"),
            nullable=False,
        ),
        sa.Column("spec_hash", sa.String(128), nullable=False),
        sa.Column("contract_hash", sa.String(128), nullable=False),
        sa.Column("normalized_claims", sa.JSON, nullable=False),
        sa.Column("explicit_refusals", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("planned_checks", sa.JSON, nullable=False),
        sa.Column("tier_cap", sa.String(32), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # Only one ACTIVE contract per registration
    op.create_index(
        "uq_active_contract_per_registration",
        "evaluation_contracts",
        ["construct_registration_id"],
        unique=True,
        postgresql_where=sa.text("status = 'ACTIVE'"),
    )

    # Lookup by contract_hash for run validation
    op.create_index(
        "ix_evaluation_contracts_contract_hash",
        "evaluation_contracts",
        ["contract_hash"],
    )

    # -- EXTEND: investigations with contract_hash --
    op.add_column(
        "investigations",
        sa.Column("contract_hash", sa.String(128), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("investigations", "contract_hash")
    op.drop_index("ix_evaluation_contracts_contract_hash", table_name="evaluation_contracts")
    op.drop_index("uq_active_contract_per_registration", table_name="evaluation_contracts")
    op.drop_table("evaluation_contracts")
