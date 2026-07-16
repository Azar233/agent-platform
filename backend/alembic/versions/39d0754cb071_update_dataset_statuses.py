"""update dataset statuses

Revision ID: 39d0754cb071
Revises: f6a7b8c9d0e1
Create Date: 2026-07-16 15:53:01.464036

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '39d0754cb071'
down_revision: Union[str, None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Migrate existing 'ready' dataset versions to the new status set.

    Uses a single offline-compatible UPDATE statement so it can run without a
    live database connection (e.g. alembic --sql).
    """
    op.execute(
        """
        UPDATE dataset_versions
        SET status = CASE
            WHEN EXISTS (
                SELECT 1 FROM training_tasks
                WHERE training_tasks.dataset_version_id = dataset_versions.id
                  AND training_tasks.status = 'running'
            ) THEN 'training'
            WHEN EXISTS (
                SELECT 1 FROM model_versions
                WHERE model_versions.dataset_version_id = dataset_versions.id
                  AND model_versions.status = 'active'
            ) THEN 'published'
            ELSE 'pending_train'
        END
        WHERE status = 'ready'
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE dataset_versions
        SET status = 'ready'
        WHERE status IN ('pending_train', 'training', 'published')
        """
    )
