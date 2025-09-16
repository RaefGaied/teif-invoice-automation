"""add notes to invoice

Revision ID: 234567890abc
Revises: 1234567890ab
Create Date: 2025-09-15 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '234567890abc'
down_revision = '1234567890ab'
branch_labels = None
depends_on = None


def upgrade():
    # Add notes column to invoices table
    op.add_column('invoices',
                 sa.Column('notes', sa.Text(),
                          nullable=True,
                          comment='Additional notes or terms for the invoice'))


def downgrade():
    # Drop notes column from invoices table
    op.drop_column('invoices', 'notes')
