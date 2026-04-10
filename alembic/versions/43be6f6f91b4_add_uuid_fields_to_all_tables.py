"""add_uuid_fields_to_all_tables

Revision ID: 43be6f6f91b4
Revises: 39e905c7e9b3
Create Date: 2025-12-09 15:30:54.163445

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '43be6f6f91b4'
down_revision = '39e905c7e9b3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Habilita extensão UUID se não estiver habilitada
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
    
    # Adiciona campo uuid em users
    op.add_column('users', sa.Column('uuid', sa.UUID(), nullable=True))
    op.execute("UPDATE users SET uuid = uuid_generate_v4() WHERE uuid IS NULL")
    op.alter_column('users', 'uuid', nullable=False)
    op.create_index(op.f('ix_users_uuid'), 'users', ['uuid'], unique=True)
    
    # Adiciona campo uuid em musics
    op.add_column('musics', sa.Column('uuid', sa.UUID(), nullable=True))
    op.execute("UPDATE musics SET uuid = uuid_generate_v4() WHERE uuid IS NULL")
    op.alter_column('musics', 'uuid', nullable=False)
    op.create_index(op.f('ix_musics_uuid'), 'musics', ['uuid'], unique=True)
    
    # Adiciona campo uuid em video_edits
    op.add_column('video_edits', sa.Column('uuid', sa.UUID(), nullable=True))
    op.execute("UPDATE video_edits SET uuid = uuid_generate_v4() WHERE uuid IS NULL")
    op.alter_column('video_edits', 'uuid', nullable=False)
    op.create_index(op.f('ix_video_edits_uuid'), 'video_edits', ['uuid'], unique=True)
    
    # Adiciona campo uuid em publication_queue
    op.add_column('publication_queue', sa.Column('uuid', sa.UUID(), nullable=True))
    op.execute("UPDATE publication_queue SET uuid = uuid_generate_v4() WHERE uuid IS NULL")
    op.alter_column('publication_queue', 'uuid', nullable=False)
    op.create_index(op.f('ix_publication_queue_uuid'), 'publication_queue', ['uuid'], unique=True)


def downgrade() -> None:
    # Remove índices
    op.drop_index(op.f('ix_publication_queue_uuid'), table_name='publication_queue')
    op.drop_index(op.f('ix_video_edits_uuid'), table_name='video_edits')
    op.drop_index(op.f('ix_musics_uuid'), table_name='musics')
    op.drop_index(op.f('ix_users_uuid'), table_name='users')
    
    # Remove colunas
    op.drop_column('publication_queue', 'uuid')
    op.drop_column('video_edits', 'uuid')
    op.drop_column('musics', 'uuid')
    op.drop_column('users', 'uuid')

