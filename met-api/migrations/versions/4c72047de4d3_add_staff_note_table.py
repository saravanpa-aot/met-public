"""add_staff_note_table

Revision ID: 4c72047de4d3
Revises: 0e043f976e2e
Create Date: 2023-01-10 12:23:47.566091

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4c72047de4d3'
down_revision = '0e043f976e2e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('staff_note',
    sa.Column('created_date', sa.DateTime(), nullable=False),
    sa.Column('updated_date', sa.DateTime(), nullable=True),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('note', sa.Text(), nullable=True),
    sa.Column('note_type', sa.String(length=50), nullable=True),
    sa.Column('survey_id', sa.Integer(), nullable=False),
    sa.Column('submission_id', sa.Integer(), nullable=False),
    sa.Column('created_by', sa.String(length=50), nullable=True),
    sa.Column('updated_by', sa.String(length=50), nullable=True),
    sa.ForeignKeyConstraint(['submission_id'], ['submission.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['survey_id'], ['survey.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('staff_note')
    # ### end Alembic commands ###
