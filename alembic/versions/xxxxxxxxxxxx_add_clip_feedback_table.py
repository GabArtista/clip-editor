"""add clip_feedback table

Revision ID: xxxxxxxxxxxx
Revises: 0b7b14e6c96d
Create Date: 2025-10-29 XX:XX:XX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "xxxxxxxxxxxx"
down_revision = "0b7b14e6c96d"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "clip_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("clip_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("video_clip_models.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("mood", sa.String(length=32), nullable=True),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_clip_feedback_clip_id", "clip_feedback", ["clip_id"])
    op.create_index("ix_clip_feedback_user_id", "clip_feedback", ["user_id"])

def downgrade():
    op.drop_index("ix_clip_feedback_clip_id", table_name="clip_feedback")
    op.drop_index("ix_clip_feedback_user_id", table_name="clip_feedback")
    op.drop_table("clip_feedback")
