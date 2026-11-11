"""add ticket idempotency

Revision ID: 49185e26e9a2
Revises: a1b2c3d4e5f6
Create Date: 2026-11-10 15:04:46.538139

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "49185e26e9a2"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Добавляем ключ покупки
    op.add_column(
        "tickets",
        sa.Column(
            "idempotency_key",
            sa.String(),
            nullable=True,
        ),
    )

    # Добавляем хеш данных запроса
    op.add_column(
        "tickets",
        sa.Column(
            "request_hash",
            sa.String(64),
            nullable=True,
        ),
    )

    # Запрещаем повторение одного ключа
    op.create_unique_constraint(
        "uq_tickets_idempotency_key",
        "tickets",
        ["idempotency_key"],
    )


def downgrade() -> None:
    # Отменяем изменения в обратном порядке
    op.drop_constraint(
        "uq_tickets_idempotency_key",
        "tickets",
        type_="unique",
    )

    op.drop_column("tickets", "request_hash")
    op.drop_column("tickets", "idempotency_key")
