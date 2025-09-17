"""merge heads

Revision ID: 9c3d4235d162
Revises: 440ceac4236b, 4d3e2f1a5b6c
Create Date: 2025-09-16 15:49:14.380128

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9c3d4235d162'
down_revision = ('440ceac4236b', '4d3e2f1a5b6c')
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
