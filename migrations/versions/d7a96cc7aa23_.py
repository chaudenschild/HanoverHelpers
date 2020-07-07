"""empty message

Revision ID: d7a96cc7aa23
Revises: a916fa4f8df8
Create Date: 2020-07-07 14:41:06.931077

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd7a96cc7aa23'
down_revision = 'a916fa4f8df8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('volunteer', sa.Column('buddy_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'volunteer', 'recipient', ['buddy_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'volunteer', type_='foreignkey')
    op.drop_column('volunteer', 'buddy_id')
    # ### end Alembic commands ###
