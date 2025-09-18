"""Rename document_status to status and update status values

Revision ID: 47a969e18c3d
Revises: 8b1d6d216929
Create Date: 2025-09-17 10:56:00.669808

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text
from sqlalchemy.dialects import mssql

# ... rest of your migration code ...
# revision identifiers, used by Alembic.
revision = '47a969e18c3d'
down_revision = '8b1d6d216929'
branch_labels = None
depends_on = None

def upgrade():
    conn = op.get_bind()
    
    # Check if status column already exists
    status_exists = conn.execute(text("""
        SELECT 1 
        FROM sys.columns 
        WHERE object_id = OBJECT_ID('invoices') 
        AND name = 'status'
    """)).scalar()
    
    document_status_exists = conn.execute(text("""
        SELECT 1 
        FROM sys.columns 
        WHERE object_id = OBJECT_ID('invoices') 
        AND name = 'document_status'
    """)).scalar()
    
    if status_exists and not document_status_exists:
        print("Status column already exists and document_status doesn't. Migration not needed.")
        # Update status values if needed
        conn.execute(text("""
            UPDATE invoices 
            SET status = 'processing'
            WHERE status = 'draft'
        """))
        return
        
    if document_status_exists:
        print("Renaming document_status to status...")
        
        # First, check if we need to drop the status column if it exists
        if status_exists:
            # If both columns exist, we need to handle data migration
            print("Both status and document_status columns exist. Migrating data...")
            
            # First, drop any indexes on document_status
            try:
                op.drop_index('idx_invoice_status', 'invoices')
            except Exception as e:
                print(f"Warning: Could not drop index idx_invoice_status: {e}")
            
            # Then drop any default constraints on document_status
            result = conn.execute(text("""
                SELECT dc.name
                FROM sys.default_constraints dc
                JOIN sys.columns c ON dc.parent_object_id = c.object_id 
                    AND dc.parent_column_id = c.column_id
                WHERE dc.parent_object_id = OBJECT_ID('invoices')
                AND c.name = 'document_status'
            """)).fetchone()
            
            if result:
                constraint_name = result[0]
                op.drop_constraint(constraint_name, 'invoices', type_='default')
            
            # Now we can drop the column
            op.drop_column('invoices', 'document_status')
        else:
            # Only document_status exists, safe to rename
            # First drop any indexes
            try:
                op.drop_index('idx_invoice_status', 'invoices')
            except Exception as e:
                print(f"Warning: Could not drop index idx_invoice_status: {e}")
            
            # Drop default constraint if it exists
            result = conn.execute(text("""
                SELECT dc.name
                FROM sys.default_constraints dc
                JOIN sys.columns c ON dc.parent_object_id = c.object_id 
                    AND dc.parent_column_id = c.column_id
                WHERE dc.parent_object_id = OBJECT_ID('invoices')
                AND c.name = 'document_status'
            """)).fetchone()
            
            if result:
                constraint_name = result[0]
                op.drop_constraint(constraint_name, 'invoices', type_='default')
            
            # Rename the column
            op.execute("EXEC sp_rename 'invoices.document_status', 'status', 'COLUMN'")
        
        # Recreate the index on the status column
        op.create_index('idx_invoice_status', 'invoices', ['status'])
        
        # Update status values
        conn.execute(text("""
            UPDATE invoices 
            SET status = 'processing'
            WHERE status = 'draft'
        """))

def downgrade():
    conn = op.get_bind()
    
    # Check if we need to rename back to document_status
    status_exists = conn.execute(text("""
        SELECT 1 
        FROM sys.columns 
        WHERE object_id = OBJECT_ID('invoices') 
        AND name = 'status'
    """)).scalar()
    
    document_status_exists = conn.execute(text("""
        SELECT 1 
        FROM sys.columns 
        WHERE object_id = OBJECT_ID('invoices') 
        AND name = 'document_status'
    """)).scalar()
    
    if status_exists and not document_status_exists:
        # Drop the index first
        try:
            op.drop_index('idx_invoice_status', 'invoices')
        except Exception as e:
            print(f"Warning: Could not drop index idx_invoice_status: {e}")
        
        # Rename the column back
        op.execute("""
            EXEC sp_rename 'invoices.status', 'document_status', 'COLUMN'
        """)
        
        # Recreate the index
        op.create_index('idx_invoice_status', 'invoices', ['document_status'])
        
        # Re-add the default constraint
        op.execute("""
            ALTER TABLE invoices 
            ADD CONSTRAINT DF_invoices_document_status 
            DEFAULT 'draft' FOR document_status
        """)
    
    # Revert status values
    conn.execute(text("""
        UPDATE invoices 
        SET document_status = 'draft'
        WHERE document_status = 'processing'
    """))                                                                                                                                                                                                                                                                                                                   