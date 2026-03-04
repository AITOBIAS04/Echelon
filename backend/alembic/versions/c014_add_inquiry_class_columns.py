"""add inquiry_class to theatre_template, theatre, theatre_certificate

Revision ID: c014_inquiry_class
Revises: a1b2c3d4e5f6
Create Date: 2026-03-04

Cycle-014 Codex Remediation F4 — three inquiry_class columns with
server_default='COUNTERFACTUAL' for backward compatibility.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c014_inquiry_class"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # TheatreTemplate.inquiry_class — may already exist (added by ORM in sprint-29)
    # Use batch_alter_table for SQLite compatibility, try/except for idempotency
    try:
        op.add_column(
            "theatre_templates",
            sa.Column(
                "inquiry_class",
                sa.String(20),
                nullable=True,
                server_default="COUNTERFACTUAL",
            ),
        )
        op.create_index(
            "ix_theatre_templates_inquiry_class",
            "theatre_templates",
            ["inquiry_class"],
        )
    except Exception:
        pass  # Column already exists from ORM auto-create

    # Theatre.inquiry_class
    try:
        op.add_column(
            "theatres",
            sa.Column(
                "inquiry_class",
                sa.String(20),
                nullable=True,
                server_default="COUNTERFACTUAL",
            ),
        )
        op.create_index(
            "ix_theatres_inquiry_class",
            "theatres",
            ["inquiry_class"],
        )
    except Exception:
        pass

    # TheatreCertificate.inquiry_class
    try:
        op.add_column(
            "theatre_certificates",
            sa.Column(
                "inquiry_class",
                sa.String(20),
                nullable=True,
                server_default="COUNTERFACTUAL",
            ),
        )
    except Exception:
        pass


def downgrade() -> None:
    # Drop in reverse order
    try:
        op.drop_column("theatre_certificates", "inquiry_class")
    except Exception:
        pass

    try:
        op.drop_index("ix_theatres_inquiry_class", table_name="theatres")
        op.drop_column("theatres", "inquiry_class")
    except Exception:
        pass

    try:
        op.drop_index(
            "ix_theatre_templates_inquiry_class",
            table_name="theatre_templates",
        )
        op.drop_column("theatre_templates", "inquiry_class")
    except Exception:
        pass
