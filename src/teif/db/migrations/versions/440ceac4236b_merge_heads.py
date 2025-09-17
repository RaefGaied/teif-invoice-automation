"""merge heads

Revision ID: 440ceac4236b
Revises: 8ec2ae64605c, 2a1b3c4d5e6f
Create Date: 2025-09-16 15:29:46.244444

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '440ceac4236b'
down_revision = ('8ec2ae64605c', '2a1b3c4d5e6f')
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
