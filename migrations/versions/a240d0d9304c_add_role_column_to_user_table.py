"""Add role column to user table

Revision ID: a240d0d9304c
Revises: b2239badf610
Create Date: 2024-07-20 17:20:07.726871

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a240d0d9304c'
down_revision = 'b2239badf610'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('inventory', schema=None) as batch_op:
        batch_op.add_column(sa.Column('location', sa.String(length=100), nullable=False))

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('role', sa.String(length=50), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('role')

    with op.batch_alter_table('inventory', schema=None) as batch_op:
        batch_op.drop_column('location')

    # ### end Alembic commands ###
