"""add_processing_upload_status

Revision ID: 39e905c7e9b3
Revises: 002_video_edits
Create Date: 2025-12-09 14:35:51.261005

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '39e905c7e9b3'
down_revision = '002_video_edits'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Adiciona novo valor ao enum videoeditstatus
    op.execute("ALTER TYPE videoeditstatus ADD VALUE IF NOT EXISTS 'processing_upload'")


def downgrade() -> None:
    # PostgreSQL não suporta remover valores de enum diretamente
    # Seria necessário recriar o enum, mas isso é complexo
    # Por enquanto, apenas documentamos que o valor permanecerá no enum
    pass

