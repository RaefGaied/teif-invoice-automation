"""Add function_code and additional_info to companies table

Revision ID: 2a1b3c4d5e6f
Revises: 1ee1ab3c5618
Create Date: 2025-09-16 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mssql
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '2a1b3c4d5e6f'
down_revision = '1ee1ab3c5618'  # The merge migration
branch_labels = None
depends_on = None


def upgrade():
    # Add function_code column
    op.add_column('companies', 
                 sa.Column('function_code', 
                          sa.String(10), 
                          nullable=True,
                          comment="Function code for TEIF (e.g., 'I-62' for seller, 'I-64' for buyer)"))
    
    # Add additional_info column as NVARCHAR(MAX) for SQL Server
    op.add_column('companies',
                 sa.Column('additional_info',
                          sa.Text().with_variant(sa.Text(), 'mssql'),
                          nullable=True,
                          comment="Additional company information in JSON format"))


def downgrade():
    # Drop the columns if we need to rollback
    op.drop_column('companies', 'function_code')
    op.drop_column('companies', 'additional_info')


# Indication pour Alembic que la migration est transactionnelle
# et peut être exécutée dans une transaction
# Cela est particulièrement important pour SQL Server
transactional = True
