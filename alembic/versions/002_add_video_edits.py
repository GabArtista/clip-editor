"""Add video_edits table

Revision ID: 002_video_edits
Revises: 001_initial
Create Date: 2025-01-09 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_video_edits'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create video_edits table
    op.create_table(
        'video_edits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('music_id', sa.Integer(), nullable=False),
        sa.Column('local_file_path', sa.String(length=500), nullable=False),
        sa.Column('s3_key', sa.String(length=500), nullable=False),
        sa.Column('s3_url', sa.String(length=500), nullable=False),
        sa.Column('preview_url', sa.String(length=500), nullable=False),
        sa.Column('status', sa.Enum('pending_approval', 'approved', 'rejected', 'published', 'expired', name='videoeditstatus'), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delete_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['music_id'], ['musics.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_video_edits_id'), 'video_edits', ['id'], unique=False)
    op.create_index(op.f('ix_video_edits_user_id'), 'video_edits', ['user_id'], unique=False)
    op.create_index(op.f('ix_video_edits_status'), 'video_edits', ['status'], unique=False)
    op.create_index(op.f('ix_video_edits_expires_at'), 'video_edits', ['expires_at'], unique=False)
    op.create_index(op.f('ix_video_edits_delete_at'), 'video_edits', ['delete_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_video_edits_delete_at'), table_name='video_edits')
    op.drop_index(op.f('ix_video_edits_expires_at'), table_name='video_edits')
    op.drop_index(op.f('ix_video_edits_status'), table_name='video_edits')
    op.drop_index(op.f('ix_video_edits_user_id'), table_name='video_edits')
    op.drop_index(op.f('ix_video_edits_id'), table_name='video_edits')
    op.drop_table('video_edits')
    op.execute('DROP TYPE IF EXISTS videoeditstatus')

