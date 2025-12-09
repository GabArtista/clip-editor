"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2025-01-09 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('webhook_url', sa.String(length=500), nullable=True),
        sa.Column('role', sa.Enum('admin', 'user', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_blocked', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Create musics table
    op.create_table(
        'musics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_musics_id'), 'musics', ['id'], unique=False)
    op.create_index(op.f('ix_musics_user_id'), 'musics', ['user_id'], unique=False)

    # Create publication_queue table
    op.create_table(
        'publication_queue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('video_path', sa.String(length=500), nullable=False),
        sa.Column('video_url', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('scheduled_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('published_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.Enum('pending', 'scheduled', 'processing', 'completed', 'failed', 'cancelled', name='publicationstatus'), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_publication_queue_id'), 'publication_queue', ['id'], unique=False)
    op.create_index(op.f('ix_publication_queue_scheduled_date'), 'publication_queue', ['scheduled_date'], unique=False)
    op.create_index(op.f('ix_publication_queue_status'), 'publication_queue', ['status'], unique=False)
    op.create_index(op.f('ix_publication_queue_user_id'), 'publication_queue', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_publication_queue_user_id'), table_name='publication_queue')
    op.drop_index(op.f('ix_publication_queue_status'), table_name='publication_queue')
    op.drop_index(op.f('ix_publication_queue_scheduled_date'), table_name='publication_queue')
    op.drop_index(op.f('ix_publication_queue_id'), table_name='publication_queue')
    op.drop_table('publication_queue')
    
    op.drop_index(op.f('ix_musics_user_id'), table_name='musics')
    op.drop_index(op.f('ix_musics_id'), table_name='musics')
    op.drop_table('musics')
    
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS publicationstatus')
    op.execute('DROP TYPE IF EXISTS userrole')

