"""add missing columns

Revision ID: 1234567890ab
Revises: af5d10f50b6f
Create Date: 2025-09-15 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1234567890ab'
down_revision = 'af5d10f50b6f'
branch_labels = None
depends_on = None

def upgrade():
    # Add reference_number to invoice_references
    op.add_column('invoice_references', 
                 sa.Column('reference_number', sa.String(length=100), 
                          nullable=False, 
                          comment='Reference number or identifier',
                          server_default=''))
    
    # Add document_number and document_url to additional_documents
    op.add_column('additional_documents',
                 sa.Column('document_number', sa.String(length=100),
                          nullable=False,
                          comment='Document number or identifier',
                          server_default=''))
    
    op.add_column('additional_documents',
                 sa.Column('document_url', sa.String(length=500),
                          nullable=True,
                          comment='URL or path to the document'))
    
    # Add columns to special_conditions
    op.add_column('special_conditions',
                 sa.Column('condition_type', sa.String(length=10),
                          nullable=False,
                          comment='Condition type code (e.g., "I-01" for Discount, "I-02" for Surcharge)',
                          server_default='I-01'))
    
    op.add_column('special_conditions',
                 sa.Column('description', sa.String(length=500),
                          nullable=False,
                          comment='Description of the special condition',
                          server_default=''))
    
    op.add_column('special_conditions',
                 sa.Column('amount', sa.Numeric(15, 3),
                          nullable=False,
                          comment='Amount of the special condition',
                          server_default='0'))
    
    op.add_column('special_conditions',
                 sa.Column('currency', sa.String(length=3),
                          nullable=False,
                          comment='Currency code (ISO 4217)',
                          server_default='TND'))


def downgrade():
    # Drop columns in reverse order
    op.drop_column('special_conditions', 'currency')
    op.drop_column('special_conditions', 'amount')
    op.drop_column('special_conditions', 'description')
    op.drop_column('special_conditions', 'condition_type')
    
    op.drop_column('additional_documents', 'document_url')
    op.drop_column('additional_documents', 'document_number')
    
    op.drop_column('invoice_references', 'reference_number')
