"""add feedback learning tables

Revision ID: 0b7b14e6c96d
Revises: 96bddc9babdd
Create Date: 2025-10-18 21:18:05.469889
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "0b7b14e6c96d"
down_revision = "96bddc9babdd"
branch_labels = None
depends_on = None


feedback_mood_enum = postgresql.ENUM(
    "positive",
    "neutral",
    "negative",
    name="feedback_mood",
    create_type=False,
)

learning_center_scope_enum = postgresql.ENUM(
    "global",
    "artist",
    "music",
    name="learning_center_scope",
    create_type=False,
)

learning_center_status_enum = postgresql.ENUM(
    "active",
    "paused",
    "archived",
    name="learning_center_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        feedback_mood_enum.create(bind, checkfirst=True)
        learning_center_scope_enum.create(bind, checkfirst=True)
        learning_center_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "music_feedback",
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
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("mood", feedback_mood_enum, nullable=True),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=True),
        sa.Column("weight", sa.Numeric(5, 2), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_music_feedback_music_asset", "music_feedback", ["music_asset_id"])
    op.create_index("ix_music_feedback_user", "music_feedback", ["user_id"])

    op.create_table(
        "artist_feedback",
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
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("mood", feedback_mood_enum, nullable=True),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=True),
        sa.Column("weight", sa.Numeric(5, 2), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_artist_feedback_user", "artist_feedback", ["user_id"])
    op.create_index("ix_artist_feedback_music", "artist_feedback", ["music_asset_id"])

    op.create_table(
        "global_genre_profiles",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("genre", sa.String(length=128), nullable=False, unique=True),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    op.create_table(
        "learning_centers",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("scope", learning_center_scope_enum, nullable=False),
        sa.Column("status", learning_center_status_enum, nullable=False, server_default=sa.text("'active'")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column(
            "music_asset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("music_assets.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("genre", sa.String(length=128), nullable=True),
        sa.Column("is_experimental", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("parameters", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("baseline_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
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
    op.create_index("ix_learning_centers_user", "learning_centers", ["user_id"])
    op.create_index("ix_learning_centers_music", "learning_centers", ["music_asset_id"])
    op.create_index("ix_learning_centers_scope", "learning_centers", ["scope"])

    op.create_table(
        "learning_center_history",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "learning_center_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("learning_centers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", learning_center_status_enum, nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index(
        "ix_learning_center_history_center",
        "learning_center_history",
        ["learning_center_id", "version"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_learning_center_history_center", table_name="learning_center_history")
    op.drop_table("learning_center_history")

    op.drop_index("ix_learning_centers_scope", table_name="learning_centers")
    op.drop_index("ix_learning_centers_music", table_name="learning_centers")
    op.drop_index("ix_learning_centers_user", table_name="learning_centers")
    op.drop_table("learning_centers")

    op.drop_table("global_genre_profiles")

    op.drop_index("ix_artist_feedback_music", table_name="artist_feedback")
    op.drop_index("ix_artist_feedback_user", table_name="artist_feedback")
    op.drop_table("artist_feedback")

    op.drop_index("ix_music_feedback_user", table_name="music_feedback")
    op.drop_index("ix_music_feedback_music_asset", table_name="music_feedback")
    op.drop_table("music_feedback")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        feedback_mood_enum.drop(bind, checkfirst=True)
        learning_center_scope_enum.drop(bind, checkfirst=True)
        learning_center_status_enum.drop(bind, checkfirst=True)
