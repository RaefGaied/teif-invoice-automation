"""Fix updated_at constraint

Revision ID: fix_updated_at_constraint
Revises: 238ba371b20d
Create Date: 2025-09-16 11:57:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mssql

# revision identifiers, used by Alembic.
revision = 'fix_updated_at_constraint'
down_revision = '238ba371b20d'
branch_labels = None
depends_on = None


def upgrade():
    # First, drop the default constraint on updated_at if it exists
    op.execute("""
    DECLARE @constraint_name NVARCHAR(256)
    SELECT @constraint_name = name 
    FROM sys.default_constraints
    WHERE parent_object_id = OBJECT_ID('companies')
    AND parent_column_id = (
        SELECT column_id 
        FROM sys.columns 
        WHERE object_id = OBJECT_ID('companies') 
        AND name = 'updated_at'
    )
    IF @constraint_name IS NOT NULL
        EXEC('ALTER TABLE companies DROP CONSTRAINT ' + @constraint_name)
    """)
    
    # Now alter the column
    op.alter_column('companies', 'updated_at',
               existing_type=mssql.DATETIME2(),
               type_=sa.DateTime(),
               nullable=True,
               existing_server_default=None)
    
    # Add back a default constraint
    op.alter_column('companies', 'updated_at',
               server_default=sa.text('GETDATE()'))

def downgrade():
    # Drop the default constraint first
    op.execute("""
    DECLARE @constraint_name NVARCHAR(256)
    SELECT @constraint_name = name 
    FROM sys.default_constraints
    WHERE parent_object_id = OBJECT_ID('companies')
    AND parent_column_id = (
        SELECT column_id 
        FROM sys.columns 
        WHERE object_id = OBJECT_ID('companies') 
        AND name = 'updated_at'
    )
    IF @constraint_name IS NOT NULL
        EXEC('ALTER TABLE companies DROP CONSTRAINT ' + @constraint_name)
    """)
    
    # Revert the column type
    op.alter_column('companies', 'updated_at',
               existing_type=sa.DateTime(),
               type_=mssql.DATETIME2(),
               nullable=True)
    
    # Add back the original default constraint
    op.alter_column('companies', 'updated_at',
               server_default=sa.text('CURRENT_TIMESTAMP'))

# Indication for Alembic that the migration is transactional
transactional = True
