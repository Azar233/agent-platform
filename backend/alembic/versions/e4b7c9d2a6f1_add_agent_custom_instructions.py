"""add user-level agent custom instructions

Revision ID: e4b7c9d2a6f1
Revises: d3f8a1c6e5b2
Create Date: 2026-07-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "e4b7c9d2a6f1"
down_revision: Union[str, Sequence[str], None] = "d3f8a1c6e5b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "agent_custom_instructions",
            sa.Text(),
            nullable=True,
            comment="用户级 Agent 响应偏好，仅用于语言、语气和输出格式",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "agent_custom_instructions")
