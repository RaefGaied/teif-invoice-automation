"""Initial migration - Fixed SQL Server constraints

Revision ID: af5d10f50b6f
Revises: 
Create Date: 2025-09-09 09:59:17.391339

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mssql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'af5d10f50b6f'
down_revision = None
branch_labels = None
depends_on = None

def has_table(table_name):
    bind = op.get_bind()
    inspector = inspect(bind)
    return inspector.has_table(table_name)

def has_column(table_name, column_name):
    if not has_table(table_name):
        return False
    bind = op.get_bind()
    inspector = inspect(bind)
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
    # Check if table exists
    if not has_table('additional_documents'):
        return
        
    # Add updated_at column if it doesn't exist
    if not has_column('additional_documents', 'updated_at'):
        op.add_column('additional_documents', 
                     sa.Column('updated_at', sa.DateTime(), nullable=True))
        op.execute("UPDATE additional_documents SET updated_at = GETDATE()")
        op.alter_column('additional_documents', 'updated_at',
                      existing_type=sa.DateTime(),
                      type_=sa.DateTime(),
                      nullable=False)
    
    # Handle created_at column modification
    if has_column('additional_documents', 'created_at'):
        # First drop the default constraint
        drop_default_constraint('additional_documents', 'created_at')
        
        # Then alter the column
        op.alter_column('additional_documents', 'created_at',
                      existing_type=mssql.DATETIME2(),
                      type_=sa.DateTime(),
                      nullable=False)
        
        # Add back the default value
        op.execute("""
        ALTER TABLE additional_documents 
        ADD CONSTRAINT DF_additional_documents_created_at 
        DEFAULT GETDATE() FOR created_at
        """)

def downgrade():
    if not has_table('additional_documents'):
        return
        
    if has_column('additional_documents', 'updated_at'):
        op.drop_column('additional_documents', 'updated_at')
        
    if has_column('additional_documents', 'created_at'):
        # Drop the default constraint first
        drop_default_constraint('additional_documents', 'created_at')
        
        # Then alter the column back to its original type
        op.alter_column('additional_documents', 'created_at',
                      existing_type=sa.DateTime(),
                      type_=mssql.DATETIME2(),
                      nullable=True)
        
        # Add back the original default constraint
        op.execute("""
        ALTER TABLE additional_documents 
        ADD CONSTRAINT DF_additional_documents_created_at 
        DEFAULT (getdate()) FOR created_at
        """)

transactional = True
