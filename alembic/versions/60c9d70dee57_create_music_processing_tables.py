"""create music processing tables

Revision ID: 60c9d70dee57
Revises: 20240901_0001
Create Date: 2025-10-18 16:51:33.849936
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "60c9d70dee57"
down_revision = "20240901_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("music_assets", sa.Column("genre_inferred", sa.String(length=128), nullable=True))
    op.add_column("music_assets", sa.Column("genre_confidence", sa.Numeric(5, 2), nullable=True))
    op.add_column("music_assets", sa.Column("analysis_version", sa.String(length=32), nullable=True))
    op.add_column("music_assets", sa.Column("analysis_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    op.create_table(
        "music_beats",
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
        sa.Column("timestamp_seconds", sa.Numeric(10, 2), nullable=False),
        sa.Column("beat_type", sa.String(length=32), nullable=False, server_default=sa.text("'beat'")),
        sa.Column("confidence", sa.Numeric(5, 2), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_music_beats_music_asset", "music_beats", ["music_asset_id"])

    op.create_table(
        "music_embeddings",
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
        sa.Column("embedding_type", sa.String(length=64), nullable=False),
        sa.Column("vector", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_music_embeddings_music_asset", "music_embeddings", ["music_asset_id"])


def downgrade() -> None:
    op.drop_index("ix_music_embeddings_music_asset", table_name="music_embeddings")
    op.drop_table("music_embeddings")

    op.drop_index("ix_music_beats_music_asset", table_name="music_beats")
    op.drop_table("music_beats")

    op.drop_column("music_assets", "analysis_summary")
    op.drop_column("music_assets", "analysis_version")
    op.drop_column("music_assets", "genre_confidence")
    op.drop_column("music_assets", "genre_inferred")
