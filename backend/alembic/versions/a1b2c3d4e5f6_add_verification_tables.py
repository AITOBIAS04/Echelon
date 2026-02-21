"""Add verification tables

Revision ID: a1b2c3d4e5f6
Revises: 347c30465dba
Create Date: 2026-02-19 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '347c30465dba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. verification_certificates (no FK dependencies except self-contained)
    op.create_table('verification_certificates',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('construct_id', sa.String(length=255), nullable=False),
        sa.Column('domain', sa.String(length=50), nullable=False),
        sa.Column('replay_count', sa.Integer(), nullable=False),
        sa.Column('precision', sa.Float(), nullable=False),
        sa.Column('recall', sa.Float(), nullable=False),
        sa.Column('reply_accuracy', sa.Float(), nullable=False),
        sa.Column('composite_score', sa.Float(), nullable=False),
        sa.Column('brier', sa.Float(), nullable=False),
        sa.Column('sample_size', sa.Integer(), nullable=False),
        sa.Column('ground_truth_source', sa.String(length=500), nullable=False),
        sa.Column('commit_range', sa.String(length=255), nullable=False),
        sa.Column('methodology_version', sa.String(length=20), nullable=False),
        sa.Column('scoring_model', sa.String(length=100), nullable=False),
        sa.Column('raw_scores_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_verification_certs_construct_created', 'verification_certificates',
                     ['construct_id', 'created_at'], unique=False)
    op.create_index('ix_verification_certs_brier', 'verification_certificates',
                     ['brier'], unique=False)
    op.create_index(op.f('ix_verification_certificates_construct_id'), 'verification_certificates',
                     ['construct_id'], unique=False)

    # 2. verification_replay_scores (FK -> certificates)
    op.create_table('verification_replay_scores',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('certificate_id', sa.String(length=50), nullable=False),
        sa.Column('ground_truth_id', sa.String(length=255), nullable=False),
        sa.Column('precision', sa.Float(), nullable=False),
        sa.Column('recall', sa.Float(), nullable=False),
        sa.Column('reply_accuracy', sa.Float(), nullable=False),
        sa.Column('claims_total', sa.Integer(), nullable=False),
        sa.Column('claims_supported', sa.Integer(), nullable=False),
        sa.Column('changes_total', sa.Integer(), nullable=False),
        sa.Column('changes_surfaced', sa.Integer(), nullable=False),
        sa.Column('scoring_model', sa.String(length=100), nullable=False),
        sa.Column('scoring_latency_ms', sa.Integer(), nullable=False),
        sa.Column('scored_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['certificate_id'], ['verification_certificates.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_verification_replay_scores_certificate_id'), 'verification_replay_scores',
                     ['certificate_id'], unique=False)

    # 3. verification_runs (FK -> users, FK -> certificates)
    op.create_table('verification_runs',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('user_id', sa.String(length=50), nullable=False),
        sa.Column('construct_id', sa.String(length=255), nullable=False),
        sa.Column('repo_url', sa.String(length=500), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'INGESTING', 'INVOKING', 'SCORING',
                                     'CERTIFYING', 'COMPLETED', 'FAILED',
                                     name='verificationrunstatus'), nullable=False),
        sa.Column('progress', sa.Integer(), nullable=False),
        sa.Column('total', sa.Integer(), nullable=False),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('certificate_id', sa.String(length=50), nullable=True),
        sa.Column('config_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['certificate_id'], ['verification_certificates.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_verification_runs_user_id'), 'verification_runs',
                     ['user_id'], unique=False)
    op.create_index(op.f('ix_verification_runs_construct_id'), 'verification_runs',
                     ['construct_id'], unique=False)
    op.create_index('ix_verification_runs_status', 'verification_runs',
                     ['status'], unique=False)
    op.create_index('ix_verification_runs_user_created', 'verification_runs',
                     ['user_id', 'created_at'], unique=False)
    op.create_index('ix_verification_runs_construct', 'verification_runs',
                     ['construct_id'], unique=False)


def downgrade() -> None:
    # Drop in reverse FK order
    op.drop_index('ix_verification_runs_construct', table_name='verification_runs')
    op.drop_index('ix_verification_runs_user_created', table_name='verification_runs')
    op.drop_index('ix_verification_runs_status', table_name='verification_runs')
    op.drop_index(op.f('ix_verification_runs_construct_id'), table_name='verification_runs')
    op.drop_index(op.f('ix_verification_runs_user_id'), table_name='verification_runs')
    op.drop_table('verification_runs')

    op.drop_index(op.f('ix_verification_replay_scores_certificate_id'), table_name='verification_replay_scores')
    op.drop_table('verification_replay_scores')

    op.drop_index(op.f('ix_verification_certificates_construct_id'), table_name='verification_certificates')
    op.drop_index('ix_verification_certs_brier', table_name='verification_certificates')
    op.drop_index('ix_verification_certs_construct_created', table_name='verification_certificates')
    op.drop_table('verification_certificates')

    # Drop the enum type
    op.execute("DROP TYPE IF EXISTS verificationrunstatus")
