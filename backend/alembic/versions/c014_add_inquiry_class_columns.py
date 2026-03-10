"""add inquiry_class to theatre_template, theatre, theatre_certificate

Revision ID: c014_inquiry_class
Revises: c012_theatre_inv_deploy
Create Date: 2026-03-04

Cycle-014 Codex Remediation F4 — three inquiry_class columns with
server_default='COUNTERFACTUAL' for backward compatibility.

FIXED 2026-03-10: Replaced try/except with inspector-based checks.
On PostgreSQL, a failed statement poisons the entire transaction,
so try/except around DDL is unsafe.  Also updated down_revision to
c012_theatre_inv_deploy (the new migration that creates these tables).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c014_inquiry_class"
down_revision: Union[str, None] = "c012_theatre_inv_deploy"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # TheatreTemplate.inquiry_class
    tt_cols = [c["name"] for c in inspector.get_columns("theatre_templates")]
    if "inquiry_class" not in tt_cols:
        op.add_column(
            "theatre_templates",
            sa.Column(
                "inquiry_class",
                sa.String(20),
                nullable=True,
                server_default="COUNTERFACTUAL",
            ),
        )
    tt_indexes = [idx["name"] for idx in inspector.get_indexes("theatre_templates")]
    if "ix_theatre_templates_inquiry_class" not in tt_indexes:
        op.create_index(
            "ix_theatre_templates_inquiry_class",
            "theatre_templates",
            ["inquiry_class"],
        )

    # Theatre.inquiry_class
    t_cols = [c["name"] for c in inspector.get_columns("theatres")]
    if "inquiry_class" not in t_cols:
        op.add_column(
            "theatres",
            sa.Column(
                "inquiry_class",
                sa.String(20),
                nullable=True,
                server_default="COUNTERFACTUAL",
            ),
        )
    t_indexes = [idx["name"] for idx in inspector.get_indexes("theatres")]
    if "ix_theatres_inquiry_class" not in t_indexes:
        op.create_index(
            "ix_theatres_inquiry_class",
            "theatres",
            ["inquiry_class"],
        )

    # TheatreCertificate.inquiry_class
    tc_cols = [c["name"] for c in inspector.get_columns("theatre_certificates")]
    if "inquiry_class" not in tc_cols:
        op.add_column(
            "theatre_certificates",
            sa.Column(
                "inquiry_class",
                sa.String(20),
                nullable=True,
                server_default="COUNTERFACTUAL",
            ),
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    tc_cols = [c["name"] for c in inspector.get_columns("theatre_certificates")]
    if "inquiry_class" in tc_cols:
        op.drop_column("theatre_certificates", "inquiry_class")

    t_indexes = [idx["name"] for idx in inspector.get_indexes("theatres")]
    if "ix_theatres_inquiry_class" in t_indexes:
        op.drop_index("ix_theatres_inquiry_class", table_name="theatres")
    t_cols = [c["name"] for c in inspector.get_columns("theatres")]
    if "inquiry_class" in t_cols:
        op.drop_column("theatres", "inquiry_class")

    tt_indexes = [idx["name"] for idx in inspector.get_indexes("theatre_templates")]
    if "ix_theatre_templates_inquiry_class" in tt_indexes:
        op.drop_index(
            "ix_theatre_templates_inquiry_class",
            table_name="theatre_templates",
        )
    tt_cols = [c["name"] for c in inspector.get_columns("theatre_templates")]
    if "inquiry_class" in tt_cols:
        op.drop_column("theatre_templates", "inquiry_class")
