"""Initial SanctionSight schema."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260410_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "raw_source_snapshot",
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("source_system", sa.String(length=50), nullable=False),
        sa.Column("dataset_name", sa.String(length=100), nullable=False),
        sa.Column("extraction_mode", sa.String(length=20), nullable=False),
        sa.Column("ingestion_ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("snapshot_path", sa.Text(), nullable=False),
        sa.Column("file_hash", sa.String(length=128), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("source_last_updated", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    )
    op.create_index("ix_raw_source_snapshot_source_system", "raw_source_snapshot", ["source_system"])
    op.create_index("ix_raw_source_snapshot_ingestion_ts", "raw_source_snapshot", ["ingestion_ts"])

    op.create_table(
        "raw_sanctions_record",
        sa.Column("raw_record_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("raw_source_snapshot.snapshot_id"), nullable=False),
        sa.Column("source_system", sa.String(length=50), nullable=False),
        sa.Column("source_record_id", sa.String(length=255), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("source_last_updated", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_raw_sanctions_record_snapshot_id", "raw_sanctions_record", ["snapshot_id"])
    op.create_index("ix_raw_sanctions_record_source_system", "raw_sanctions_record", ["source_system"])
    op.create_index("ix_raw_sanctions_record_source_record_id", "raw_sanctions_record", ["source_record_id"])
    op.create_index("ix_raw_sanctions_record_ingested_at", "raw_sanctions_record", ["ingested_at"])

    op.create_table(
        "raw_blackrock_fund_record",
        sa.Column("raw_record_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("raw_source_snapshot.snapshot_id"), nullable=False),
        sa.Column("source_record_id", sa.String(length=255), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_raw_blackrock_fund_record_snapshot_id", "raw_blackrock_fund_record", ["snapshot_id"])
    op.create_index("ix_raw_blackrock_fund_record_source_record_id", "raw_blackrock_fund_record", ["source_record_id"])
    op.create_index("ix_raw_blackrock_fund_record_ingested_at", "raw_blackrock_fund_record", ["ingested_at"])

    op.create_table(
        "raw_blackrock_holding_record",
        sa.Column("raw_record_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("raw_source_snapshot.snapshot_id"), nullable=False),
        sa.Column("source_record_id", sa.String(length=255), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_raw_blackrock_holding_record_snapshot_id", "raw_blackrock_holding_record", ["snapshot_id"])
    op.create_index("ix_raw_blackrock_holding_record_source_record_id", "raw_blackrock_holding_record", ["source_record_id"])
    op.create_index("ix_raw_blackrock_holding_record_ingested_at", "raw_blackrock_holding_record", ["ingested_at"])

    op.create_table(
        "screening_run",
        sa.Column("run_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column("total_funds_screened", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_holdings_screened", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_sanctions_entities", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("candidate_matches_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("high_match_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("medium_match_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("low_match_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("stale_source_warning_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_screening_run_started_at", "screening_run", ["started_at"])
    op.create_index("ix_screening_run_status", "screening_run", ["status"])

    op.create_table(
        "screening_match",
        sa.Column("match_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("screening_run.run_id"), nullable=False),
        sa.Column("fund_id", sa.String(length=255), nullable=False),
        sa.Column("holding_id", sa.String(length=255), nullable=False),
        sa.Column("sanctions_entity_id", sa.String(length=255), nullable=False),
        sa.Column("source_system", sa.String(length=50), nullable=False),
        sa.Column("match_type", sa.String(length=50), nullable=False),
        sa.Column("raw_score", sa.Float(), nullable=False),
        sa.Column("confidence_band", sa.String(length=20), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("review_status", sa.String(length=20), nullable=False, server_default="Pending"),
        sa.Column("reviewer_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_screening_match_run_id", "screening_match", ["run_id"])
    op.create_index("ix_screening_match_fund_id", "screening_match", ["fund_id"])
    op.create_index("ix_screening_match_holding_id", "screening_match", ["holding_id"])
    op.create_index("ix_screening_match_sanctions_entity_id", "screening_match", ["sanctions_entity_id"])
    op.create_index("ix_screening_match_source_system", "screening_match", ["source_system"])
    op.create_index("ix_screening_match_confidence_band", "screening_match", ["confidence_band"])
    op.create_index("ix_screening_match_created_at", "screening_match", ["created_at"])

    op.create_table(
        "screening_match_evidence",
        sa.Column("evidence_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("match_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("screening_match.match_id"), nullable=False),
        sa.Column("evidence_type", sa.String(length=50), nullable=False),
        sa.Column("evidence_key", sa.String(length=100), nullable=False),
        sa.Column("evidence_value", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_screening_match_evidence_match_id", "screening_match_evidence", ["match_id"])
    op.create_index("ix_screening_match_evidence_created_at", "screening_match_evidence", ["created_at"])

    op.create_table(
        "data_quality_issue",
        sa.Column("issue_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_system", sa.String(length=50), nullable=False),
        sa.Column("check_name", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("issue_message", sa.Text(), nullable=False),
        sa.Column("affected_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("observed_value", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_data_quality_issue_run_id", "data_quality_issue", ["run_id"])
    op.create_index("ix_data_quality_issue_source_system", "data_quality_issue", ["source_system"])
    op.create_index("ix_data_quality_issue_created_at", "data_quality_issue", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_data_quality_issue_created_at", table_name="data_quality_issue")
    op.drop_index("ix_data_quality_issue_source_system", table_name="data_quality_issue")
    op.drop_index("ix_data_quality_issue_run_id", table_name="data_quality_issue")
    op.drop_table("data_quality_issue")

    op.drop_index("ix_screening_match_evidence_created_at", table_name="screening_match_evidence")
    op.drop_index("ix_screening_match_evidence_match_id", table_name="screening_match_evidence")
    op.drop_table("screening_match_evidence")

    op.drop_index("ix_screening_match_created_at", table_name="screening_match")
    op.drop_index("ix_screening_match_confidence_band", table_name="screening_match")
    op.drop_index("ix_screening_match_source_system", table_name="screening_match")
    op.drop_index("ix_screening_match_sanctions_entity_id", table_name="screening_match")
    op.drop_index("ix_screening_match_holding_id", table_name="screening_match")
    op.drop_index("ix_screening_match_fund_id", table_name="screening_match")
    op.drop_index("ix_screening_match_run_id", table_name="screening_match")
    op.drop_table("screening_match")

    op.drop_index("ix_screening_run_status", table_name="screening_run")
    op.drop_index("ix_screening_run_started_at", table_name="screening_run")
    op.drop_table("screening_run")

    op.drop_index("ix_raw_blackrock_holding_record_ingested_at", table_name="raw_blackrock_holding_record")
    op.drop_index("ix_raw_blackrock_holding_record_source_record_id", table_name="raw_blackrock_holding_record")
    op.drop_index("ix_raw_blackrock_holding_record_snapshot_id", table_name="raw_blackrock_holding_record")
    op.drop_table("raw_blackrock_holding_record")

    op.drop_index("ix_raw_blackrock_fund_record_ingested_at", table_name="raw_blackrock_fund_record")
    op.drop_index("ix_raw_blackrock_fund_record_source_record_id", table_name="raw_blackrock_fund_record")
    op.drop_index("ix_raw_blackrock_fund_record_snapshot_id", table_name="raw_blackrock_fund_record")
    op.drop_table("raw_blackrock_fund_record")

    op.drop_index("ix_raw_sanctions_record_ingested_at", table_name="raw_sanctions_record")
    op.drop_index("ix_raw_sanctions_record_source_record_id", table_name="raw_sanctions_record")
    op.drop_index("ix_raw_sanctions_record_source_system", table_name="raw_sanctions_record")
    op.drop_index("ix_raw_sanctions_record_snapshot_id", table_name="raw_sanctions_record")
    op.drop_table("raw_sanctions_record")

    op.drop_index("ix_raw_source_snapshot_ingestion_ts", table_name="raw_source_snapshot")
    op.drop_index("ix_raw_source_snapshot_source_system", table_name="raw_source_snapshot")
    op.drop_table("raw_source_snapshot")

