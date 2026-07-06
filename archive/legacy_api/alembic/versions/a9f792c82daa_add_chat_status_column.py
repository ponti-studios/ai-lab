"""add chat status column

Revision ID: a9f792c82daa
Revises: 31656ae66c49
Create Date: 2024-08-09 08:51:44.958584

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9f792c82daa'
down_revision: Union[str, None] = '31656ae66c49'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the new type
    op.execute('CREATE TYPE chatstate AS ENUM (\'ACTIVE\', \'INACTIVE\', \'ENDED\')')
    # Add the column with a default value for existing rows
    op.execute('ALTER TABLE chats ADD COLUMN state chatstate NOT NULL DEFAULT \'ACTIVE\'')


def downgrade() -> None:
    # Drop the column
    op.execute('DROP TYPE chatstate')
    # Drop the type
    op.execute('ALTER TABLE chats DROP COLUMN state')
