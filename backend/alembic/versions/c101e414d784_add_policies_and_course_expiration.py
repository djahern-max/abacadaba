"""add policies table and course expiration date

Revision ID: c101e414d784
Revises: 89972a5eb2c4
Create Date: 2026-08-23 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c101e414d784'
down_revision: Union[str, None] = '89972a5eb2c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Kept in sync by hand with app/constants/policies.py - see that file's
# docstring. Alembic migrations must not import application code, since the
# constant's own text could change after this migration has already shipped.
PLACEHOLDER_BODY = "This policy has not been written yet."
SEEDED_POLICIES = [
    ("refund-and-cancellation", "Refund and Cancellation Policy"),
    ("complaint-resolution", "Complaint Resolution Policy"),
    ("records-retention", "Records Retention Policy"),
    ("program-cancellation", "Program Cancellation Policy"),
]


def upgrade() -> None:
    op.create_table(
        'policies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_policies_slug'), 'policies', ['slug'], unique=True)

    op.add_column('courses', sa.Column('expires_on', sa.Date(), nullable=True))

    # Seeded as an explicit, unmistakably-unwritten placeholder rather than
    # plausible-looking policy text - see current-feature.md, "Seed the rows
    # with an explicit placeholder, not with plausible policy text." A fresh
    # database refuses to publish any course until an admin replaces these.
    policies_table = sa.table(
        'policies',
        sa.column('slug', sa.String),
        sa.column('title', sa.String),
        sa.column('body', sa.Text),
    )
    op.bulk_insert(
        policies_table,
        [{"slug": slug, "title": title, "body": PLACEHOLDER_BODY} for slug, title in SEEDED_POLICIES],
    )


def downgrade() -> None:
    op.drop_column('courses', 'expires_on')
    op.drop_index(op.f('ix_policies_slug'), table_name='policies')
    op.drop_table('policies')
