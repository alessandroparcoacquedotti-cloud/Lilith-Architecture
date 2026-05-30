from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260601_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "replay_runs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("run_id", sa.String(length=128), nullable=False),
        sa.Column("replay_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="PENDING", nullable=False),
        sa.Column("fixtures_processed", sa.Integer(), server_default="0", nullable=False),
        sa.UniqueConstraint("run_id"),
    )
    op.create_index("ix_replay_runs_run_id", "replay_runs", ["run_id"], unique=True)
    op.create_index("ix_replay_runs_replay_timestamp", "replay_runs", ["replay_timestamp"], unique=False)
    op.create_index("ix_replay_runs_created_at", "replay_runs", ["created_at"], unique=False)
    op.create_index("ix_replay_runs_status", "replay_runs", ["status"], unique=False)

    op.create_table(
        "artifact_records",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("run_id", sa.String(length=128), nullable=False),
        sa.Column("artifact_type", sa.String(length=64), nullable=False),
        sa.Column("artifact_path", sa.String(length=512), nullable=False),
        sa.Column("integrity_hash", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["replay_runs.run_id"], ondelete="CASCADE"),
        sa.UniqueConstraint("run_id", "artifact_type", "artifact_path"),
    )
    op.create_index("ix_artifact_records_run_id", "artifact_records", ["run_id"], unique=False)
    op.create_index("ix_artifact_records_artifact_type", "artifact_records", ["artifact_type"], unique=False)
    op.create_index("ix_artifact_records_integrity_hash", "artifact_records", ["integrity_hash"], unique=False)
    op.create_index("ix_artifact_records_created_at", "artifact_records", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_artifact_records_created_at", table_name="artifact_records")
    op.drop_index("ix_artifact_records_integrity_hash", table_name="artifact_records")
    op.drop_index("ix_artifact_records_artifact_type", table_name="artifact_records")
    op.drop_index("ix_artifact_records_run_id", table_name="artifact_records")
    op.drop_table("artifact_records")

    op.drop_index("ix_replay_runs_status", table_name="replay_runs")
    op.drop_index("ix_replay_runs_created_at", table_name="replay_runs")
    op.drop_index("ix_replay_runs_replay_timestamp", table_name="replay_runs")
    op.drop_index("ix_replay_runs_run_id", table_name="replay_runs")
    op.drop_table("replay_runs")
