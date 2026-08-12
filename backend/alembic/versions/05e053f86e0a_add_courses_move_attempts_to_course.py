"""add courses, move attempts to course

Revision ID: 05e053f86e0a
Revises: af95594e5536
Create Date: 2026-08-12 03:58:59.283456

No data migration here on purpose. Both the local and production databases
were confirmed empty (0 rows in attempts, 0 rows in lessons) on 2026-08-12,
right before this revision was written, so there is nothing to backfill for
the new courses table, the new not-null lessons.course_id/position columns,
or the lesson_id -> course_id rename on attempts. If this ever needs to run
against a database that already has rows, it will fail loudly on the
not-null columns rather than silently drop data - that is intentional.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05e053f86e0a'
down_revision: Union[str, None] = 'af95594e5536'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'courses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('is_published', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('thumbnail_key', sa.String(), nullable=True),
        sa.Column('retake_cooldown_minutes', sa.Integer(), server_default='0', nullable=False),
        sa.Column('max_attempts', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_courses_slug'), 'courses', ['slug'], unique=True)

    op.add_column('lessons', sa.Column('course_id', sa.Integer(), nullable=False))
    op.add_column('lessons', sa.Column('position', sa.Integer(), nullable=False))
    op.create_index(op.f('ix_lessons_course_id'), 'lessons', ['course_id'], unique=False)
    op.create_unique_constraint('uq_lessons_course_id_position', 'lessons', ['course_id', 'position'])
    op.create_foreign_key(
        'lessons_course_id_fkey', 'lessons', 'courses', ['course_id'], ['id'], ondelete='CASCADE'
    )
    op.drop_column('lessons', 'retake_cooldown_minutes')
    op.drop_column('lessons', 'max_attempts')

    op.add_column('attempts', sa.Column('course_id', sa.Integer(), nullable=False))
    op.create_index(op.f('ix_attempts_course_id'), 'attempts', ['course_id'], unique=False)
    op.drop_constraint('attempts_lesson_id_fkey', 'attempts', type_='foreignkey')
    op.create_foreign_key(
        'attempts_course_id_fkey', 'attempts', 'courses', ['course_id'], ['id'], ondelete='CASCADE'
    )
    op.drop_index('ix_attempts_lesson_id', table_name='attempts')
    op.drop_column('attempts', 'lesson_id')


def downgrade() -> None:
    op.add_column('attempts', sa.Column('lesson_id', sa.INTEGER(), autoincrement=False, nullable=False))
    op.create_index('ix_attempts_lesson_id', 'attempts', ['lesson_id'], unique=False)
    op.drop_constraint('attempts_course_id_fkey', 'attempts', type_='foreignkey')
    op.create_foreign_key(
        'attempts_lesson_id_fkey', 'attempts', 'lessons', ['lesson_id'], ['id'], ondelete='CASCADE'
    )
    op.drop_index(op.f('ix_attempts_course_id'), table_name='attempts')
    op.drop_column('attempts', 'course_id')

    op.add_column(
        'lessons',
        sa.Column('max_attempts', sa.INTEGER(), autoincrement=False, nullable=True),
    )
    op.add_column(
        'lessons',
        sa.Column(
            'retake_cooldown_minutes', sa.INTEGER(), server_default=sa.text('0'), autoincrement=False, nullable=False
        ),
    )
    op.drop_constraint('lessons_course_id_fkey', 'lessons', type_='foreignkey')
    op.drop_constraint('uq_lessons_course_id_position', 'lessons', type_='unique')
    op.drop_index(op.f('ix_lessons_course_id'), table_name='lessons')
    op.drop_column('lessons', 'position')
    op.drop_column('lessons', 'course_id')

    op.drop_index(op.f('ix_courses_slug'), table_name='courses')
    op.drop_table('courses')
