"""create video suggestion tables

Revision ID: 96bddc9babdd
Revises: 60c9d70dee57
Create Date: 2025-10-18 17:29:27.064212
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "96bddc9babdd"
down_revision = "60c9d70dee57"
branch_labels = None
depends_on = None

asset_status_enum = postgresql.ENUM(
    "pending",
    "processing",
    "ready",
    "failed",
    "archived",
    name="asset_status",
    create_type=False,
)


def upgrade() -> None:
    op.create_table(
        "video_ingests",
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
            "music_asset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("music_assets.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("source_url", sa.String(length=1024), nullable=False),
        sa.Column("storage_path", sa.String(length=1024), nullable=True),
        sa.Column("duration_seconds", sa.Numeric(10, 2), nullable=True),
        sa.Column("status", asset_status_enum, nullable=False, server_default=sa.text("'pending'::asset_status")),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
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
    op.create_index("ix_video_ingests_user_id", "video_ingests", ["user_id"])
    op.create_index("ix_video_ingests_status", "video_ingests", ["status"])

    op.create_table(
        "video_analysis",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "video_ingest_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("video_ingests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("scene_breakdown", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("motion_stats", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("keywords", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_video_analysis_video_ingest", "video_analysis", ["video_ingest_id"])

    op.create_table(
        "video_clip_models",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "video_ingest_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("video_ingests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "music_asset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("music_assets.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("option_order", sa.Integer(), nullable=False),
        sa.Column("variant_label", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("video_segments", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("music_start_seconds", sa.Numeric(10, 2), nullable=True),
        sa.Column("music_end_seconds", sa.Numeric(10, 2), nullable=True),
        sa.Column("diversity_tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("score", sa.Numeric(5, 2), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_video_clip_models_video", "video_clip_models", ["video_ingest_id"])
    op.create_index("ix_video_clip_models_music", "video_clip_models", ["music_asset_id"])
    op.create_index(
        "ix_video_clip_models_option",
        "video_clip_models",
        ["video_ingest_id", "option_order"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_video_clip_models_option", table_name="video_clip_models")
    op.drop_index("ix_video_clip_models_music", table_name="video_clip_models")
    op.drop_index("ix_video_clip_models_video", table_name="video_clip_models")
    op.drop_table("video_clip_models")

    op.drop_index("ix_video_analysis_video_ingest", table_name="video_analysis")
    op.drop_table("video_analysis")

    op.drop_index("ix_video_ingests_status", table_name="video_ingests")
    op.drop_index("ix_video_ingests_user_id", table_name="video_ingests")
    op.drop_table("video_ingests")
