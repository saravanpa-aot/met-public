"""email queue

Revision ID: 587badc69491
Revises: d2e7baa531ce
Create Date: 2023-06-05 06:17:14.373765

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '587badc69491'
down_revision = 'd2e7baa531ce'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('email_queue',
    sa.Column('created_date', sa.DateTime(), nullable=False),
    sa.Column('updated_date', sa.DateTime(), nullable=True),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('entity_id', sa.Integer(), nullable=False),
    sa.Column('entity_type', sa.String(length=100), nullable=False),
    sa.Column('action', sa.String(length=100), nullable=True),
    sa.Column('notification_status', sa.Enum('PROCESSING', 'SENT', name='notificationstatus'), nullable=True),
    sa.Column('created_by', sa.String(length=50), nullable=True),
    sa.Column('updated_by', sa.String(length=50), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('email_queue')
    # ### end Alembic commands ###
