"""Add discount_percent to invoice_lines

Revision ID: 4d3e2f1a5b6c
Revises: 1ee1ab3c5618
Create Date: 2025-09-16 15:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mssql

# revision identifiers, used by Alembic.
revision = '4d3e2f1a5b6c'
down_revision = '1ee1ab3c5618'  # The merge migration
branch_labels = None
depends_on = None


def upgrade():
    # Add discount_percent column to invoice_lines
    op.add_column('invoice_lines',
                 sa.Column('discount_percent',
                          sa.Numeric(5, 2, asdecimal=True),
                          nullable=True,
                          comment="Discount percentage (0-100)"))


def downgrade():
    # Drop the column if rolling back
    op.drop_column('invoice_lines', 'discount_percent')


# Indication pour Alembic que la migration est transactionnelle
# et peut être exécutée dans une transaction
# Cela est particulièrement important pour SQL Server
transactional = True
