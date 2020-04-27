"""empty message

Revision ID: d4f5ec707401
Revises: d39dab5e5016
Create Date: 2020-04-27 12:07:38.051979

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4f5ec707401'
down_revision = 'd39dab5e5016'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('transaction', sa.Column('modification_count', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('transaction', 'modification_count')
    # ### end Alembic commands ###
