"""018 Scenario Packs Engine — 7 new tables + Theatre extension

Revision ID: c018_scenario_packs
Revises: c017_policy_surface
Create Date: 2026-03-07

Sprint-0 migration:
- Create scenario_pack_templates table
- Create scenario_checkpoints table
- Create checkpoint_branches table
- Create scenario_packs table
- Create scenario_runs table
- Create run_checkpoint_results table
- Create scenario_pack_audit_events table
- Add spawned_from_checkpoint_id to theatres
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c018_scenario_packs"
down_revision: Union[str, None] = "c017_policy_surface"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # ── 1. scenario_pack_templates ──
    if "scenario_pack_templates" not in existing_tables:
        op.create_table(
            "scenario_pack_templates",
            sa.Column("id", sa.String(100), primary_key=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("description", sa.Text, nullable=True),
            sa.Column("family", sa.String(20), nullable=False),
            sa.Column("fantasy", sa.Text, nullable=True),
            sa.Column("training_primitives", sa.Text, nullable=True),
            sa.Column("objective_vector_json", sa.JSON, nullable=True),
            sa.Column("fork_point_schema_json", sa.JSON, nullable=True),
            sa.Column("saboteur_deck_json", sa.JSON, nullable=True),
            sa.Column("telemetry_spec_json", sa.JSON, nullable=True),
            sa.Column("settlement_rules_json", sa.JSON, nullable=True),
            sa.Column("episode_length_sec", sa.Integer, nullable=True),
            sa.Column("fork_points_min", sa.Integer, nullable=False, server_default="1"),
            sa.Column("fork_points_max", sa.Integer, nullable=False, server_default="10"),
            sa.Column("settlement_latency_sec", sa.Integer, nullable=True),
            sa.Column("template_status", sa.String(20), nullable=False, server_default="CATALOG_ONLY"),
            sa.Column("is_seeded", sa.Boolean, nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime, nullable=False),
        )
        op.create_index("ix_scenario_pack_templates_family", "scenario_pack_templates", ["family"])
        op.create_index("ix_scenario_pack_templates_status", "scenario_pack_templates", ["template_status"])

    # ── 2. scenario_checkpoints ──
    if "scenario_checkpoints" not in existing_tables:
        op.create_table(
            "scenario_checkpoints",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column("template_id", sa.String(100), sa.ForeignKey("scenario_pack_templates.id"), nullable=False),
            sa.Column("sequence_num", sa.Integer, nullable=False),
            sa.Column("trigger", sa.String(255), nullable=False),
            sa.Column("trigger_condition_json", sa.JSON, nullable=True),
            sa.Column("market_question", sa.Text, nullable=False),
            sa.Column("decision_window_sec", sa.Integer, nullable=False, server_default="30"),
            sa.Column("can_spawn_theatre", sa.Boolean, nullable=False, server_default="0"),
            sa.Column("evaluator_type", sa.String(30), nullable=False, server_default="BINARY_RISK_GATE"),
            sa.Column("theatre_spawn_rule_json", sa.JSON, nullable=True),
            sa.Column("reward_mapping_json", sa.JSON, nullable=True),
            sa.Column("created_at", sa.DateTime, nullable=False),
        )
        op.create_index("ix_scenario_checkpoints_template_seq", "scenario_checkpoints", ["template_id", "sequence_num"])

    # ── 3. checkpoint_branches ──
    if "checkpoint_branches" not in existing_tables:
        op.create_table(
            "checkpoint_branches",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column("checkpoint_id", sa.String(50), sa.ForeignKey("scenario_checkpoints.id"), nullable=False),
            sa.Column("label", sa.String(255), nullable=False),
            sa.Column("branch_rule_json", sa.JSON, nullable=True),
            sa.Column("outcome_type", sa.String(20), nullable=False),
            sa.Column("reward_mapping_json", sa.JSON, nullable=True),
            sa.Column("next_checkpoint_id", sa.String(50), sa.ForeignKey("scenario_checkpoints.id"), nullable=True),
        )
        op.create_index("ix_checkpoint_branches_checkpoint", "checkpoint_branches", ["checkpoint_id"])

    # ── 4. scenario_packs ──
    if "scenario_packs" not in existing_tables:
        op.create_table(
            "scenario_packs",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column("user_id", sa.String(50), nullable=False),
            sa.Column("template_id", sa.String(100), sa.ForeignKey("scenario_pack_templates.id"), nullable=False),
            sa.Column("state", sa.String(20), nullable=False, server_default="DRAFT"),
            sa.Column("commitment_hash", sa.String(128), nullable=True),
            sa.Column("committed_at", sa.DateTime, nullable=True),
            sa.Column("resolved_at", sa.DateTime, nullable=True),
            sa.Column("run_mode", sa.String(30), nullable=False, server_default="TRAINING"),
            sa.Column("agent_assignment", sa.String(50), nullable=False, server_default="auto_assign"),
            sa.Column("simulation_scale", sa.String(20), nullable=False, server_default="single_1x"),
            sa.Column("objective_profile", sa.String(50), nullable=False, server_default="pack_default"),
            sa.Column("config_json", sa.JSON, nullable=True),
            sa.Column("created_at", sa.DateTime, nullable=False),
            sa.Column("updated_at", sa.DateTime, nullable=False),
        )
        op.create_index("ix_scenario_packs_state", "scenario_packs", ["state"])
        op.create_index("ix_scenario_packs_user", "scenario_packs", ["user_id"])
        op.create_index("ix_scenario_packs_template", "scenario_packs", ["template_id"])

    # ── 5. scenario_runs ──
    if "scenario_runs" not in existing_tables:
        op.create_table(
            "scenario_runs",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column("pack_id", sa.String(50), sa.ForeignKey("scenario_packs.id"), nullable=False),
            sa.Column("agent_id", sa.String(50), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
            sa.Column("environment_seed", sa.Integer, nullable=True),
            sa.Column("run_mode", sa.String(20), nullable=False, server_default="TRAINING"),
            sa.Column("current_checkpoint_seq", sa.Integer, nullable=False, server_default="0"),
            sa.Column("started_at", sa.DateTime, nullable=True),
            sa.Column("completed_at", sa.DateTime, nullable=True),
            sa.Column("telemetry_json", sa.JSON, nullable=True),
            sa.Column("episode_duration_sec", sa.Float, nullable=True),
            sa.Column("total_reward", sa.Float, nullable=False, server_default="0.0"),
            sa.Column("created_at", sa.DateTime, nullable=False),
        )
        op.create_index("ix_scenario_runs_pack", "scenario_runs", ["pack_id"])
        op.create_index("ix_scenario_runs_status", "scenario_runs", ["status"])

    # ── 6. run_checkpoint_results ──
    if "run_checkpoint_results" not in existing_tables:
        op.create_table(
            "run_checkpoint_results",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column("run_id", sa.String(50), sa.ForeignKey("scenario_runs.id"), nullable=False),
            sa.Column("checkpoint_id", sa.String(50), sa.ForeignKey("scenario_checkpoints.id"), nullable=False),
            sa.Column("selected_branch_id", sa.String(50), sa.ForeignKey("checkpoint_branches.id"), nullable=False),
            sa.Column("agent_decision_json", sa.JSON, nullable=True),
            sa.Column("reward", sa.Float, nullable=False, server_default="0.0"),
            sa.Column("state_vector_json", sa.JSON, nullable=True),
            sa.Column("spawned_theatre_id", sa.String(50), sa.ForeignKey("theatres.id"), nullable=True),
            sa.Column("resolved_at", sa.DateTime, nullable=False),
        )
        op.create_index("ix_run_checkpoint_results_run", "run_checkpoint_results", ["run_id"])

    # ── 7. scenario_pack_audit_events ──
    if "scenario_pack_audit_events" not in existing_tables:
        op.create_table(
            "scenario_pack_audit_events",
            sa.Column("id", sa.String(50), primary_key=True),
            sa.Column("pack_id", sa.String(50), sa.ForeignKey("scenario_packs.id"), nullable=False),
            sa.Column("event_type", sa.String(50), nullable=False),
            sa.Column("detail_json", sa.JSON, nullable=True),
            sa.Column("created_at", sa.DateTime, nullable=False),
        )
        op.create_index("ix_scenario_pack_audit_event_type", "scenario_pack_audit_events", ["event_type"])
        op.create_index("ix_scenario_pack_audit_pack_created", "scenario_pack_audit_events", ["pack_id", "created_at"])

    # ── 8. Theatre extension: spawned_from_checkpoint_id ──
    theatre_cols = [c["name"] for c in inspector.get_columns("theatres")]
    if "spawned_from_checkpoint_id" not in theatre_cols:
        op.add_column(
            "theatres",
            sa.Column(
                "spawned_from_checkpoint_id",
                sa.String(50),
                sa.ForeignKey("scenario_checkpoints.id"),
                nullable=True,
            ),
        )


def downgrade() -> None:
    # Remove Theatre extension
    op.drop_column("theatres", "spawned_from_checkpoint_id")

    # Drop tables in reverse dependency order
    op.drop_table("scenario_pack_audit_events")
    op.drop_table("run_checkpoint_results")
    op.drop_table("scenario_runs")
    op.drop_table("scenario_packs")
    op.drop_table("checkpoint_branches")
    op.drop_table("scenario_checkpoints")
    op.drop_table("scenario_pack_templates")
