"""merge 1084fd56b437 and fix_updated_at_constraint

Revision ID: 1ee1ab3c5618
Revises: 1084fd56b437, fix_updated_at_constraint
Create Date: 2025-09-16 11:58:43.397666

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1ee1ab3c5618'
down_revision = ('1084fd56b437', 'fix_updated_at_constraint')
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
