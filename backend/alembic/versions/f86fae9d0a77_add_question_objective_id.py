"""add question objective_id

Revision ID: f86fae9d0a77
Revises: 19665ec864ab
Create Date: 2026-08-23 11:11:27.750056

Hand-named the FK (autogenerate leaves create_foreign_key's name as None,
which works for create but leaves nothing for downgrade's drop_constraint to
target without a naming_convention on the metadata, which this project
doesn't set) and hand-set ondelete='SET NULL', not CASCADE. Every other FK
in this schema cascades from its parent, so autogenerate and habit both push
toward CASCADE here - it would be wrong: deleting a learning objective would
silently delete every question that tested it. SET NULL untags the question
instead, and publish validation reports the resulting coverage gap
(app/services/objective_coverage.py).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f86fae9d0a77'
down_revision: Union[str, None] = '19665ec864ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('questions', sa.Column('objective_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_questions_objective_id'), 'questions', ['objective_id'], unique=False)
    op.create_foreign_key(
        'fk_questions_objective_id',
        'questions',
        'learning_objectives',
        ['objective_id'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint('fk_questions_objective_id', 'questions', type_='foreignkey')
    op.drop_index(op.f('ix_questions_objective_id'), table_name='questions')
    op.drop_column('questions', 'objective_id')
