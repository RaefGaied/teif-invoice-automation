"""merge heads

Revision ID: 8b1d6d216929
Revises: 9c3d4235d162, 5e6f4d3c2b1a
Create Date: 2025-09-16 16:03:43.142078

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8b1d6d216929'
down_revision = ('9c3d4235d162', '5e6f4d3c2b1a')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass

# Indication pour Alembic que la migration est transactionnelle
# et peut être exécutée dans une transaction
# Cela est particulièrement important pour SQL Server
transactional = True
