"""add registry_status to sponsor_profile and its certificate snapshot

Revision ID: 2f6c9b1a4d3e
Revises: c101e414d784
Create Date: 2026-08-24 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f6c9b1a4d3e'
down_revision: Union[str, None] = 'c101e414d784'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'sponsor_profile',
        sa.Column('registry_status', sa.String(), server_default='not_registered', nullable=False),
    )
    # Hand-added: autogenerate does not write CHECK constraints.
    op.create_check_constraint(
        "ck_sponsor_profile_registry_status_valid",
        "sponsor_profile",
        "registry_status IN ('not_registered', 'registered')",
    )

    # Feature 027's certificate snapshot column, alongside the other cert_*
    # columns 024 added - nullable for the same reason: an attempt claimed
    # before this feature shipped never wrote one, and app/services/
    # certificates.py::_to_data falls back to a live read for those.
    op.add_column('attempts', sa.Column('cert_registry_status', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('attempts', 'cert_registry_status')
    op.drop_constraint("ck_sponsor_profile_registry_status_valid", "sponsor_profile", type_="check")
    op.drop_column('sponsor_profile', 'registry_status')
