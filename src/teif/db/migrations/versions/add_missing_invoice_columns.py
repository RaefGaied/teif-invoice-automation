"""Add missing invoice columns

Revision ID: add_missing_invoice_columns
Revises: 1ee1ab3c5618
Create Date: 2025-09-16 15:37:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mssql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'add_missing_invoice_columns'
down_revision = '1ee1ab3c5618'
branch_labels = None
depends_on = None

def has_column(table_name, column_name):
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table(table_name):
        return False
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def drop_default_constraint(table_name, column_name):
    """Drop default constraint for a column if it exists"""
    op.execute(f"""
    DECLARE @constraint_name NVARCHAR(256)
    SELECT @constraint_name = name 
    FROM sys.default_constraints 
    WHERE parent_object_id = OBJECT_ID('{table_name}')
    AND parent_column_id = (
        SELECT column_id 
        FROM sys.columns 
        WHERE object_id = OBJECT_ID('{table_name}') 
        AND name = '{column_name}'
    )
    
    IF @constraint_name IS NOT NULL
    BEGIN
        DECLARE @sql NVARCHAR(2000)
        SET @sql = 'ALTER TABLE {table_name} DROP CONSTRAINT ' + @constraint_name
        EXEC sp_executesql @sql
    END
    """)

def upgrade():
    # Add document_status column if it doesn't exist
    if not has_column('invoices', 'document_status'):
        op.add_column('invoices', 
            sa.Column('document_status', sa.String(20), 
                     server_default='draft',
                     nullable=False,
                     comment="Current status of the invoice")
        )
        # Create index on document_status
        op.create_index('idx_invoice_status', 'invoices', ['document_status'])
    
    # Add delivery_party_id column if it doesn't exist
    if not has_column('invoices', 'delivery_party_id'):
        op.add_column('invoices',
            sa.Column('delivery_party_id', sa.Integer(), 
                     sa.ForeignKey('companies.id'),
                     nullable=True,
                     comment="Delivery party ID if different from customer (I-66)")
        )
        # Create index on delivery_party_id
        op.create_index('idx_invoice_delivery_party', 'invoices', ['delivery_party_id'])
    
    # Add payment_terms column if it doesn't exist
    if not has_column('invoices', 'payment_terms'):
        op.add_column('invoices',
            sa.Column('payment_terms', sa.Text(),
                     nullable=True,
                     comment="Payment terms and conditions (I-37)")
        )
    
    # Add payment_means_code column if it doesn't exist
    if not has_column('invoices', 'payment_means_code'):
        op.add_column('invoices',
            sa.Column('payment_means_code', sa.String(10),
                     nullable=True,
                     comment="Payment means code (I-38)")
        )
    
    # Add payment_means_text column if it doesn't exist
    if not has_column('invoices', 'payment_means_text'):
        op.add_column('invoices',
            sa.Column('payment_means_text', sa.String(255),
                     nullable=True,
                     comment="Payment means description")
        )
    
    # Add additional_info column if it doesn't exist
    if not has_column('invoices', 'additional_info'):
        op.add_column('invoices',
            sa.Column('additional_info', mssql.NVARCHAR(),
                     nullable=True,
                     comment="Additional TEIF-specific information in JSON format")
        )
    
    # Add teif_version if it doesn't exist
    if not has_column('invoices', 'teif_version'):
        op.add_column('invoices',
            sa.Column('teif_version', sa.String(10),
                     server_default='1.8.8',
                     nullable=False,
                     comment="TEIF standard version (I-08)")
        )
    
    # Add controlling_agency if it doesn't exist
    if not has_column('invoices', 'controlling_agency'):
        op.add_column('invoices',
            sa.Column('controlling_agency', sa.String(10),
                     server_default='TTN',
                     nullable=False,
                     comment="Controlling agency (e.g., TTN) (I-09)")
        )
    
    # Add document_type_label if it doesn't exist
    if not has_column('invoices', 'document_type_label'):
        op.add_column('invoices',
            sa.Column('document_type_label', sa.String(100),
                     server_default='Facture',
                     nullable=False,
                     comment="Document type label (I-12)")
        )

def downgrade():
    # Drop indexes first
    if has_column('invoices', 'document_status'):
        op.drop_index('idx_invoice_status', 'invoices')
    
    if has_column('invoices', 'delivery_party_id'):
        op.drop_index('idx_invoice_delivery_party', 'invoices')
    
    # Drop columns in reverse order of creation
    columns_to_drop = [
        'document_status',
        'delivery_party_id',
        'payment_terms',
        'payment_means_code',
        'payment_means_text',
        'additional_info',
        'teif_version',
        'controlling_agency',
        'document_type_label'
    ]
    
    for column in columns_to_drop:
        if has_column('invoices', column):
            op.drop_column('invoices', column)
