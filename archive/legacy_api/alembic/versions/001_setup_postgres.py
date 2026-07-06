"""Create uuid-ossp extension

Revision ID: 001_create_uuid_ossp
Revises: 
Create Date: 2024-07-30 15:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "001_create_uuid_ossp"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')


def downgrade():
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
