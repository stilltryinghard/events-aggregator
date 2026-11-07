"""Добавление таблицы outbox."""

import sqlalchemy as sa

from alembic import op

revision = "a1b2c3d4e5f6"
down_revision = "7b03306c15e2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создаём таблицу для хранения событий
    op.create_table(
        "outbox",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "status",
            sa.String(),
            server_default="pending",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Индекс для быстрого поиска ожидающих событий
    op.create_index(
        "ix_outbox_status",
        "outbox",
        ["status"],
    )


def downgrade() -> None:
    # Удаляем индекс
    op.drop_index("ix_outbox_status", table_name="outbox")

    # Удаляем таблицу
    op.drop_table("outbox")
