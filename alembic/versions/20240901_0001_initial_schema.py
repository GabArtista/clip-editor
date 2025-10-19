"""initial schema

Revision ID: 20240901_0001
Revises:
Create Date: 2024-09-01 00:01:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20240901_0001"
down_revision = None
branch_labels = None
depends_on = None


ENUM_DEFINITIONS: dict[str, tuple[str, ...]] = {
    "user_status": ("active", "invited", "suspended", "deleted"),
    "social_provider": ("instagram",),
    "social_status": ("active", "expired", "revoked"),
    "asset_status": ("pending", "processing", "ready", "failed", "archived"),
    "edit_status": ("draft", "queued", "processing", "delivered", "approved", "reedit_requested", "rejected"),
    "decision_type": ("approved", "approved_with_idea", "rejected"),
}

user_status_enum = postgresql.ENUM(*ENUM_DEFINITIONS["user_status"], name="user_status", create_type=False)
social_provider_enum = postgresql.ENUM(*ENUM_DEFINITIONS["social_provider"], name="social_provider", create_type=False)
social_status_enum = postgresql.ENUM(*ENUM_DEFINITIONS["social_status"], name="social_status", create_type=False)
asset_status_enum = postgresql.ENUM(*ENUM_DEFINITIONS["asset_status"], name="asset_status", create_type=False)
edit_status_enum = postgresql.ENUM(*ENUM_DEFINITIONS["edit_status"], name="edit_status", create_type=False)
decision_type_enum = postgresql.ENUM(*ENUM_DEFINITIONS["decision_type"], name="decision_type", create_type=False)


def _create_enum_if_missing(connection, name: str, values: tuple[str, ...]) -> None:
    exists = connection.execute(
        sa.text("SELECT 1 FROM pg_type WHERE typname = :name"),
        {"name": name},
    ).scalar()

    if exists:
        return

    values_sql = ", ".join(f"'{value}'" for value in values)
    stmt = sa.text(f"CREATE TYPE {name} AS ENUM ({values_sql})")
    connection.execute(stmt)


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":  # pragma: no cover - apenas Postgres precisa da extensão
        op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    connection = op.get_bind()
    for enum_name, enum_values in ENUM_DEFINITIONS.items():
        _create_enum_if_missing(connection, enum_name, enum_values)

    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column(
            "status",
            user_status_enum,
            nullable=False,
            server_default=sa.text("'active'::user_status"),
        ),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_users_status", "users", ["status"])

    op.create_table(
        "user_profiles",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("avatar_url", sa.String(length=1024), nullable=True),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column("locale", sa.String(length=16), nullable=False, server_default=sa.text("'pt-BR'")),
        sa.Column(
            "timezone",
            sa.String(length=64),
            nullable=False,
            server_default=sa.text("'America/Sao_Paulo'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    op.create_table(
        "audio_files",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("storage_path", sa.String(length=1024), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("mime_type", sa.String(length=128), nullable=True),
        sa.Column("duration_seconds", sa.Numeric(10, 2), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_audio_files_user_id", "audio_files", ["user_id"])
    op.create_index("ix_audio_files_checksum", "audio_files", ["checksum"])

    op.create_table(
        "social_accounts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", social_provider_enum, nullable=False),
        sa.Column("provider_user_id", sa.String(length=255), nullable=True),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("cookies_encrypted", sa.Text(), nullable=True),
        sa.Column("cookies_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            social_status_enum,
            nullable=False,
            server_default=sa.text("'active'::social_status"),
        ),
        sa.Column(
            "reauth_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("error_notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index(
        "ix_social_accounts_user_provider",
        "social_accounts",
        ["user_id", "provider"],
        unique=True,
    )
    op.create_index("ix_social_accounts_status", "social_accounts", ["status"])

    op.create_table(
        "music_assets",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "audio_file_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("audio_files.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("genre", sa.String(length=128), nullable=True),
        sa.Column("bpm", sa.SmallInteger(), nullable=True),
        sa.Column("musical_key", sa.String(length=32), nullable=True),
        sa.Column(
            "status",
            asset_status_enum,
            nullable=False,
            server_default=sa.text("'pending'::asset_status"),
        ),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_music_assets_user_status", "music_assets", ["user_id", "status"])
    op.create_index("ix_music_assets_title", "music_assets", ["title"])

    op.create_table(
        "music_transcriptions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "music_asset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("music_assets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("transcript_text", sa.Text(), nullable=True),
        sa.Column("transcript_json", postgresql.JSONB(), nullable=True),
        sa.Column(
            "language",
            sa.String(length=8),
            nullable=False,
            server_default=sa.text("'pt'"),
        ),
        sa.Column("model_version", sa.String(length=64), nullable=True),
        sa.Column("confidence", sa.Numeric(5, 2), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_music_transcriptions_asset", "music_transcriptions", ["music_asset_id"])

    op.create_table(
        "reels_ingests",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "social_account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("social_accounts.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "provider",
            social_provider_enum,
            nullable=False,
            server_default=sa.text("'instagram'::social_provider"),
        ),
        sa.Column("reel_id", sa.String(length=255), nullable=True),
        sa.Column("reel_url", sa.String(length=1024), nullable=False),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("storage_path", sa.String(length=1024), nullable=True),
        sa.Column("storage_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            asset_status_enum,
            nullable=False,
            server_default=sa.text("'pending'::asset_status"),
        ),
        sa.Column("downloaded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_reels_ingests_user_provider", "reels_ingests", ["user_id", "provider"])
    op.create_index("ix_reels_ingests_reel_id", "reels_ingests", ["reel_id"], unique=True)
    op.create_index(
        "ix_reels_ingests_storage_expires",
        "reels_ingests",
        ["storage_expires_at"],
    )

    op.create_table(
        "video_scene_analysis",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "reels_ingest_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("reels_ingests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("start_time_seconds", sa.Numeric(10, 2), nullable=True),
        sa.Column("end_time_seconds", sa.Numeric(10, 2), nullable=True),
        sa.Column("keyframes", postgresql.JSONB(), nullable=True),
        sa.Column("visual_concepts", postgresql.JSONB(), nullable=True),
        sa.Column("sentiment", sa.String(length=64), nullable=True),
        sa.Column("confidence", sa.Numeric(5, 2), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index(
        "ix_video_scene_analysis_ingest",
        "video_scene_analysis",
        ["reels_ingest_id"],
    )

    op.create_table(
        "video_edits",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "reels_ingest_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("reels_ingests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "music_asset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("music_assets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "status",
            edit_status_enum,
            nullable=False,
            server_default=sa.text("'draft'::edit_status"),
        ),
        sa.Column("workflow_version", sa.String(length=64), nullable=True),
        sa.Column("ai_plan", postgresql.JSONB(), nullable=True),
        sa.Column("render_context", postgresql.JSONB(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index(
        "ix_video_edits_user_status",
        "video_edits",
        ["user_id", "status"],
    )
    op.create_index(
        "ix_video_edits_ingest_music",
        "video_edits",
        ["reels_ingest_id", "music_asset_id"],
    )

    op.create_table(
        "video_edit_segments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "video_edit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("video_edits.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("segment_order", sa.Integer(), nullable=False),
        sa.Column("video_start_seconds", sa.Numeric(10, 2), nullable=True),
        sa.Column("video_end_seconds", sa.Numeric(10, 2), nullable=True),
        sa.Column("music_start_seconds", sa.Numeric(10, 2), nullable=True),
        sa.Column("music_end_seconds", sa.Numeric(10, 2), nullable=True),
        sa.Column("ai_rationale", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Numeric(5, 2), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index(
        "ix_video_edit_segments_order",
        "video_edit_segments",
        ["video_edit_id", "segment_order"],
        unique=True,
    )

    op.create_table(
        "video_edit_deliveries",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "video_edit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("video_edits.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("delivery_url", sa.String(length=2048), nullable=False),
        sa.Column("url_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "download_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("last_download_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index(
        "ix_video_edit_deliveries_edit",
        "video_edit_deliveries",
        ["video_edit_id"],
    )
    op.create_index(
        "ix_video_edit_deliveries_expires",
        "video_edit_deliveries",
        ["url_expires_at"],
    )

    op.create_table(
        "user_feedback",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "video_edit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("video_edits.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("decision", decision_type_enum, nullable=False),
        sa.Column("feedback_text", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_user_feedback_edit", "user_feedback", ["video_edit_id"])
    op.create_index(
        "ix_user_feedback_user_decision",
        "user_feedback",
        ["user_id", "decision"],
    )

    op.create_table(
        "reedit_requests",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "original_edit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("video_edits.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "new_edit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("video_edits.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("prompt_text", sa.Text(), nullable=False),
        sa.Column("context_snapshot", postgresql.JSONB(), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    op.create_table(
        "ai_learning_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column(
            "weight",
            sa.Numeric(5, 2),
            nullable=False,
            server_default=sa.text("1.0"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    op.create_table(
        "audit_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("entity_name", sa.String(length=255), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index(
        "ix_audit_logs_entity",
        "audit_logs",
        ["entity_name", "entity_id"],
    )
    op.create_index("ix_audit_logs_user", "audit_logs", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_user", table_name="audit_logs")
    op.drop_index("ix_audit_logs_entity", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_table("ai_learning_events")

    op.drop_table("reedit_requests")

    op.drop_index("ix_user_feedback_user_decision", table_name="user_feedback")
    op.drop_index("ix_user_feedback_edit", table_name="user_feedback")
    op.drop_table("user_feedback")

    op.drop_index("ix_video_edit_deliveries_expires", table_name="video_edit_deliveries")
    op.drop_index("ix_video_edit_deliveries_edit", table_name="video_edit_deliveries")
    op.drop_table("video_edit_deliveries")

    op.drop_index("ix_video_edit_segments_order", table_name="video_edit_segments")
    op.drop_table("video_edit_segments")

    op.drop_index("ix_video_edits_ingest_music", table_name="video_edits")
    op.drop_index("ix_video_edits_user_status", table_name="video_edits")
    op.drop_table("video_edits")

    op.drop_index("ix_video_scene_analysis_ingest", table_name="video_scene_analysis")
    op.drop_table("video_scene_analysis")

    op.drop_index("ix_reels_ingests_storage_expires", table_name="reels_ingests")
    op.drop_index("ix_reels_ingests_reel_id", table_name="reels_ingests")
    op.drop_index("ix_reels_ingests_user_provider", table_name="reels_ingests")
    op.drop_table("reels_ingests")

    op.drop_index("ix_music_transcriptions_asset", table_name="music_transcriptions")
    op.drop_table("music_transcriptions")

    op.drop_index("ix_music_assets_title", table_name="music_assets")
    op.drop_index("ix_music_assets_user_status", table_name="music_assets")
    op.drop_table("music_assets")

    op.drop_index("ix_social_accounts_status", table_name="social_accounts")
    op.drop_index("ix_social_accounts_user_provider", table_name="social_accounts")
    op.drop_table("social_accounts")

    op.drop_index("ix_audio_files_checksum", table_name="audio_files")
    op.drop_index("ix_audio_files_user_id", table_name="audio_files")
    op.drop_table("audio_files")

    op.drop_table("user_profiles")

    op.drop_index("ix_users_status", table_name="users")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS decision_type")
    op.execute("DROP TYPE IF EXISTS edit_status")
    op.execute("DROP TYPE IF EXISTS asset_status")
    op.execute("DROP TYPE IF EXISTS social_status")
    op.execute("DROP TYPE IF EXISTS social_provider")
    op.execute("DROP TYPE IF EXISTS user_status")

    op.execute("DROP EXTENSION IF EXISTS pgcrypto")
