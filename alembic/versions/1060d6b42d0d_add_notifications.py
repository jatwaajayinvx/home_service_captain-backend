"""add notifications

Revision ID: 1060d6b42d0d
Revises: 8520dd2010b9
Create Date: 2026-09-24 16:50:41.105004
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision: str = "1060d6b42d0d"
down_revision: Union[str, Sequence[str], None] = "8520dd2010b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add booking reference
    op.add_column(
        "notifications",
        sa.Column(
            "booking_id",
            sa.BigInteger(),
            nullable=True,
        ),
    )

    # Match SQLAlchemy model
    op.alter_column(
        "notifications",
        "title",
        existing_type=mysql.VARCHAR(
            length=200,
            collation="utf8mb4_unicode_ci",
        ),
        type_=sa.String(length=150),
        existing_nullable=False,
    )

    op.alter_column(
        "notifications",
        "message",
        existing_type=mysql.VARCHAR(
            length=1000,
            collation="utf8mb4_unicode_ci",
        ),
        type_=sa.Text(),
        existing_nullable=False,
    )

    op.alter_column(
        "notifications",
        "notification_type",
        existing_type=mysql.VARCHAR(
            length=50,
            collation="utf8mb4_unicode_ci",
        ),
        nullable=False,
    )

    op.alter_column(
        "notifications",
        "is_read",
        existing_type=mysql.TINYINT(display_width=1),
        nullable=False,
        existing_server_default=sa.text("'0'"),
    )

    # Index
    op.create_index(
        "ix_notifications_id",
        "notifications",
        ["id"],
        unique=False,
    )

    # Booking foreign key
    op.create_foreign_key(
        "fk_notification_booking",
        "notifications",
        "bookings",
        ["booking_id"],
        ["id"],
    )


def downgrade() -> None:
    # Remove booking foreign key
    op.drop_constraint(
        "fk_notification_booking",
        "notifications",
        type_="foreignkey",
    )

    # Remove index
    op.drop_index(
        "ix_notifications_id",
        table_name="notifications",
    )

    # Restore original column definitions
    op.alter_column(
        "notifications",
        "is_read",
        existing_type=mysql.TINYINT(display_width=1),
        nullable=True,
        existing_server_default=sa.text("'0'"),
    )

    op.alter_column(
        "notifications",
        "notification_type",
        existing_type=mysql.VARCHAR(
            length=50,
            collation="utf8mb4_unicode_ci",
        ),
        nullable=True,
    )

    op.alter_column(
        "notifications",
        "message",
        existing_type=sa.Text(),
        type_=mysql.VARCHAR(
            length=1000,
            collation="utf8mb4_unicode_ci",
        ),
        existing_nullable=False,
    )

    op.alter_column(
        "notifications",
        "title",
        existing_type=sa.String(length=150),
        type_=mysql.VARCHAR(
            length=200,
            collation="utf8mb4_unicode_ci",
        ),
        existing_nullable=False,
    )

    # Remove booking reference
    op.drop_column(
        "notifications",
        "booking_id",
    )