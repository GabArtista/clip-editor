"""simple schema for wallet + music

Revision ID: 20241109_0001
Revises:
Create Date: 2024-11-09 02:35:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20241109_0001"
down_revision = None
branch_labels = None
depends_on = None

user_status_enum = sa.Enum("active", "suspended", "deleted", name="user_status")
wallet_transaction_type_enum = sa.Enum("deposit", "usage", name="wallet_transaction_type")


def upgrade() -> None:
    bind = op.get_bind()
    user_status_enum.create(bind, checkfirst=True)
    wallet_transaction_type_enum.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("status", user_status_enum, nullable=False, server_default=sa.text("'active'::user_status")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "user_music",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("audio_storage_path", sa.String(length=1024), nullable=False),
        sa.Column("duration_seconds", sa.Numeric(10, 2), nullable=True),
        sa.Column("bpm", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_user_music_user_id", "user_music", ["user_id"])

    op.create_table(
        "wallet_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default=sa.text("'BRL'")),
        sa.Column("balance_credits", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "music_transcriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_music_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_music.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("language", sa.String(length=8), nullable=False, server_default=sa.text("'pt'")),
        sa.Column("transcript_text", sa.Text(), nullable=True),
        sa.Column("transcript_json", postgresql.JSONB(), nullable=True),
        sa.Column("generated_by", sa.String(length=128), nullable=True),
        sa.Column("confidence", sa.Numeric(5, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_music_transcriptions_music", "music_transcriptions", ["user_music_id"], unique=True)

    op.create_table(
        "wallet_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "wallet_account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("wallet_accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("transaction_type", wallet_transaction_type_enum, nullable=False),
        sa.Column("amount_credits", sa.Numeric(12, 2), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_wallet_transactions_wallet", "wallet_transactions", ["wallet_account_id"])


def downgrade() -> None:
    op.drop_index("ix_wallet_transactions_wallet", table_name="wallet_transactions")
    op.drop_table("wallet_transactions")

    op.drop_index("ix_music_transcriptions_music", table_name="music_transcriptions")
    op.drop_table("music_transcriptions")

    op.drop_table("wallet_accounts")

    op.drop_index("ix_user_music_user_id", table_name="user_music")
    op.drop_table("user_music")

    op.drop_table("users")

    bind = op.get_bind()
    wallet_transaction_type_enum.drop(bind, checkfirst=True)
    user_status_enum.drop(bind, checkfirst=True)
