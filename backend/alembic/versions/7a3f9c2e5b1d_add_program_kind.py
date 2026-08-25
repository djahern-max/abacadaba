"""add program_kind to courses and its certificate snapshot

Revision ID: 7a3f9c2e5b1d
Revises: 2f6c9b1a4d3e
Create Date: 2026-08-24 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a3f9c2e5b1d'
down_revision: Union[str, None] = '2f6c9b1a4d3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'courses',
        sa.Column('program_kind', sa.String(), server_default='cpe', nullable=False),
    )
    # Hand-added: autogenerate does not write CHECK constraints.
    op.create_check_constraint(
        "ck_courses_program_kind_valid",
        "courses",
        "program_kind IN ('cpe', 'general')",
    )

    # Feature 029's certificate snapshot column, alongside the other cert_*
    # columns 024 added and 027 followed for cert_registry_status - nullable
    # for the same reason: an attempt claimed before this feature shipped
    # never wrote one, and app/services/certificates.py::_to_data falls back
    # to 'cpe' for those, since every certificate claimed before this
    # feature shipped was in fact issued for a CPE-presented course.
    op.add_column('attempts', sa.Column('cert_program_kind', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('attempts', 'cert_program_kind')
    op.drop_constraint("ck_courses_program_kind_valid", "courses", type_="check")
    op.drop_column('courses', 'program_kind')
