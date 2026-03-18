"""Initial schema — auth, registry, results tables.

Revision ID: 0001
Revises: None
Create Date: 2026-03-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- auth schema ---
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("username", sa.String(150), unique=True, nullable=False, index=True),
        sa.Column("hashed_password", sa.Text, nullable=False),
        sa.Column("is_active", sa.Boolean, server_default="true", nullable=False),
        sa.Column("is_admin", sa.Boolean, server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        schema="auth",
    )
    op.create_table(
        "user_preferences",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("value", postgresql.JSONB, nullable=True),
        schema="auth",
    )

    # --- registry schema ---
    op.create_table(
        "layers",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("key", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("enabled", sa.Boolean, server_default="true", nullable=False),
        sa.Column("sort_order", sa.Integer, server_default="0", nullable=False),
        schema="registry",
    )
    op.create_table(
        "tools",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("key", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("layer_id", sa.Integer, sa.ForeignKey("registry.layers.id"), nullable=False),
        sa.Column("queue", sa.String(100), nullable=False),
        sa.Column("task", sa.String(200), nullable=False),
        sa.Column("enabled", sa.Boolean, server_default="true", nullable=False),
        sa.Column("deferred", sa.Boolean, server_default="false", nullable=False),
        sa.Column("container_service", sa.String(100), nullable=True),
        schema="registry",
    )
    op.create_table(
        "presets",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("key", sa.String(150), unique=True, nullable=False, index=True),
        sa.Column("tool_id", sa.Integer, sa.ForeignKey("registry.tools.id"), nullable=False),
        sa.Column("label", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("example_file", sa.String(200), nullable=False),
        sa.Column("enabled", sa.Boolean, server_default="true", nullable=False),
        schema="registry",
    )
    op.create_table(
        "couplings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("key", sa.String(150), unique=True, nullable=False, index=True),
        sa.Column("from_tool_id", sa.Integer, sa.ForeignKey("registry.tools.id"), nullable=False),
        sa.Column("to_tool_id", sa.Integer, sa.ForeignKey("registry.tools.id"), nullable=False),
        sa.Column("coupling_type", sa.String(50), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("default_param_map", postgresql.JSONB, nullable=True),
        sa.Column("enabled", sa.Boolean, server_default="true", nullable=False),
        sa.Column("deferred", sa.Boolean, server_default="false", nullable=False),
        sa.Column("coupling_tool", sa.String(100), nullable=True),
        schema="registry",
    )
    op.create_table(
        "pipelines",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("key", sa.String(150), unique=True, nullable=False, index=True),
        sa.Column("label", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("enabled", sa.Boolean, server_default="true", nullable=False),
        schema="registry",
    )
    op.create_table(
        "pipeline_steps",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("pipeline_id", sa.Integer, sa.ForeignKey("registry.pipelines.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_order", sa.Integer, nullable=False),
        sa.Column("tool_id", sa.Integer, sa.ForeignKey("registry.tools.id"), nullable=False),
        sa.Column("label", sa.String(200), nullable=True),
        sa.Column("params", postgresql.JSONB, nullable=True),
        sa.Column("param_map", postgresql.JSONB, nullable=True),
        schema="registry",
    )
    op.create_table(
        "pipeline_presets",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("key", sa.String(150), unique=True, nullable=False, index=True),
        sa.Column("pipeline_id", sa.Integer, sa.ForeignKey("registry.pipelines.id"), nullable=False),
        sa.Column("label", sa.String(200), nullable=False),
        sa.Column("example_file", sa.String(200), nullable=False),
        sa.Column("enabled", sa.Boolean, server_default="true", nullable=False),
        schema="registry",
    )
    op.create_table(
        "coupling_presets",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("key", sa.String(150), unique=True, nullable=False, index=True),
        sa.Column("coupling_id", sa.Integer, sa.ForeignKey("registry.couplings.id"), nullable=False),
        sa.Column("label", sa.String(200), nullable=False),
        sa.Column("from_tool_key", sa.String(100), nullable=False),
        sa.Column("to_tool_key", sa.String(100), nullable=False),
        sa.Column("example_file", sa.String(200), nullable=False),
        sa.Column("enabled", sa.Boolean, server_default="true", nullable=False),
        schema="registry",
    )

    # --- results schema ---
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(200), unique=True, nullable=False, index=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        schema="results",
    )
    op.create_table(
        "simulation_runs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("job_id", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("results.projects.id"), nullable=False),
        sa.Column("tool_key", sa.String(100), nullable=False),
        sa.Column("label", sa.String(500), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="PENDING"),
        sa.Column("params_summary", sa.Text, nullable=True),
        sa.Column("duration_s", sa.Float, nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("result_path", sa.String(500), nullable=True),
        sa.Column("result_size_bytes", sa.Integer, nullable=True),
        sa.Column("submitted_by", sa.String(150), nullable=True),
        sa.Column("pipeline_run_id", sa.String(100), nullable=True),
        sa.Column("sweep_run_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        schema="results",
    )
    op.create_index(
        "ix_simulation_runs_composite",
        "simulation_runs",
        ["project_id", "tool_key", "status", sa.text("created_at DESC")],
        schema="results",
    )
    op.create_table(
        "pipeline_runs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("pipeline_id", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("pipeline_type", sa.String(50), nullable=False),
        sa.Column("project_name", sa.String(200), nullable=False),
        sa.Column("label", sa.String(500), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="RUNNING"),
        sa.Column("total_steps", sa.Integer, nullable=False),
        sa.Column("current_step", sa.Integer, server_default="0", nullable=False),
        sa.Column("variables", postgresql.JSONB, nullable=True),
        sa.Column("steps_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        schema="results",
    )
    op.create_table(
        "sweep_runs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("sweep_id", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("tool_key", sa.String(100), nullable=False),
        sa.Column("project_name", sa.String(200), nullable=False),
        sa.Column("method", sa.String(50), nullable=False),
        sa.Column("total_runs", sa.Integer, nullable=False),
        sa.Column("completed_runs", sa.Integer, server_default="0", nullable=False),
        sa.Column("failed_runs", sa.Integer, server_default="0", nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="RUNNING"),
        sa.Column("runs_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        schema="results",
    )
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("action", sa.String(100), nullable=False, index=True),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.String(200), nullable=True),
        sa.Column("username", sa.String(150), nullable=True),
        sa.Column("details", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, index=True),
        schema="results",
    )


def downgrade() -> None:
    op.drop_table("audit_log", schema="results")
    op.drop_table("sweep_runs", schema="results")
    op.drop_table("pipeline_runs", schema="results")
    op.drop_index("ix_simulation_runs_composite", table_name="simulation_runs", schema="results")
    op.drop_table("simulation_runs", schema="results")
    op.drop_table("projects", schema="results")
    op.drop_table("coupling_presets", schema="registry")
    op.drop_table("pipeline_presets", schema="registry")
    op.drop_table("pipeline_steps", schema="registry")
    op.drop_table("pipelines", schema="registry")
    op.drop_table("couplings", schema="registry")
    op.drop_table("presets", schema="registry")
    op.drop_table("tools", schema="registry")
    op.drop_table("layers", schema="registry")
    op.drop_table("user_preferences", schema="auth")
    op.drop_table("users", schema="auth")
