"""Add additional_info to invoice_lines

Revision ID: 5e6f4d3c2b1a
Revises: 440ceac4236b
Create Date: 2025-09-16 15:50:25.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mssql

# revision identifiers, used by Alembic.
revision = '5e6f4d3c2b1a'
down_revision = '440ceac4236b'
branch_labels = None
depends_on = None

def upgrade():
    # Add additional_info column to invoice_lines
    op.add_column('invoice_lines',
                 sa.Column('additional_info',
                          sa.Text(),
                          nullable=True,
                          comment="Additional information in JSON format"))

def downgrade():
    op.drop_column('invoice_lines', 'additional_info')

# Transactional DDL for SQL Server
transactional = True