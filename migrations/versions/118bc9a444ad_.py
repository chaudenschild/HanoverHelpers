"""empty message

Revision ID: 118bc9a444ad
Revises: 008804b399d4
Create Date: 2020-05-03 16:25:04.412281

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '118bc9a444ad'
down_revision = '008804b399d4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('userdirectory', 'username',
                    existing_type=sa.VARCHAR(length=64),
                    nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('userdirectory', 'username',
                    existing_type=sa.VARCHAR(length=64),
                    nullable=False)
    # ### end Alembic commands ###
