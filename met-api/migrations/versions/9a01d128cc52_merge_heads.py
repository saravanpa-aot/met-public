"""merge heads

Revision ID: 9a01d128cc52
Revises: e5fceb8c33c6, 6764af39864e
Create Date: 2022-12-15 00:13:06.739170

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9a01d128cc52'
down_revision = ('e5fceb8c33c6', '6764af39864e')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
