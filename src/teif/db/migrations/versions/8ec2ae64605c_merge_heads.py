"""merge heads

Revision ID: 8ec2ae64605c
Revises: 100bff5dd299, add_missing_invoice_columns
Create Date: 2025-09-16 14:46:49.421298

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8ec2ae64605c'
down_revision = ('100bff5dd299', 'add_missing_invoice_columns')
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
