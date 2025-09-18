"""rename document_status to status

Revision ID: 08a5ae99d56f
Revises: f43ea5dfa431
Create Date: 2025-09-17 11:42:00.837052

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '08a5ae99d56f'
down_revision = 'f43ea5dfa431'
branch_labels = None
depends_on = None


def upgrade():
    # Rename the column
    op.alter_column(
        'invoices', 
        'document_status',
        new_column_name='status',
        existing_type=sa.String(20)
    )
    
    # Update existing status values
    op.execute("""
        UPDATE invoices 
        SET status = 'processing'
        WHERE status = 'draft'
    """)
    
    op.execute("""
        UPDATE invoices 
        SET status = 'generated'
        WHERE status = 'processed'
    """)


def downgrade():
    # Revert status values
    op.execute("""
        UPDATE invoices 
        SET status = 'processed'
        WHERE status = 'generated'
    """)
    
    op.execute("""
        UPDATE invoices 
        SET status = 'draft'
        WHERE status = 'processing'
    """)
    
    # Rename the column back
    op.alter_column(
        'invoices', 
        'status',
        new_column_name='document_status',
        existing_type=sa.String(20)
    )
# Indication pour Alembic que la migration est transactionnelle
# et peut être exécutée dans une transaction
# Cela est particulièrement important pour SQL Server
transactional = True
