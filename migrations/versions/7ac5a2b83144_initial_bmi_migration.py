"""Initial BMI migration

Revision ID: 7ac5a2b83144
Revises: 
Create Date: 2025-07-20 13:57:30.575798

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7ac5a2b83144'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('activity',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('image', sa.String(length=200), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('child',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('age', sa.Integer(), nullable=False),
    sa.Column('parent_contact', sa.String(length=100), nullable=False),
    sa.Column('class_name', sa.String(length=100), nullable=True),
    sa.Column('birth_date', sa.String(length=20), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('email', sa.String(length=100), nullable=True),
    sa.Column('phone', sa.String(length=20), nullable=True),
    sa.Column('password', sa.String(length=100), nullable=True),
    sa.Column('student_code', sa.String(length=20), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('student_code')
    )
    op.create_table('curriculum',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('week_number', sa.Integer(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('material', sa.String(length=200), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('staff',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('position', sa.String(length=100), nullable=False),
    sa.Column('contact_info', sa.String(length=100), nullable=False),
    sa.Column('email', sa.String(length=100), nullable=True),
    sa.Column('phone', sa.String(length=20), nullable=True),
    sa.Column('password', sa.String(length=100), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('attendance_record',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('child_id', sa.Integer(), nullable=False),
    sa.Column('date', sa.String(length=20), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.ForeignKeyConstraint(['child_id'], ['child.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('bmi_record',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('student_id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('weight', sa.Float(), nullable=False),
    sa.Column('height', sa.Float(), nullable=False),
    sa.Column('bmi', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['student_id'], ['child.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('bmi_record')
    op.drop_table('attendance_record')
    op.drop_table('staff')
    op.drop_table('curriculum')
    op.drop_table('child')
    op.drop_table('activity')
    # ### end Alembic commands ###
