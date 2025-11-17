"""Placeholder migration to restore missing revision c1f2a3b4d5e6

This file is intentionally empty: it registers the missing revision id
so Alembic can continue working. Use only if you have confirmed the
database already contains the schema changes that this revision would
have applied. Always back up the database before applying.

Revision ID: c1f2a3b4d5e6
Revises: 5855c033b93f
Create Date: 2025-11-16 00:00:00.000000
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'c1f2a3b4d5e6'
down_revision = '5855c033b93f'
branch_labels = None
depends_on = None


def upgrade():
    """Placeholder upgrade: no operations.

    The database is assumed to already contain the changes this revision
    would have applied. This file only restores Alembic's revision graph.
    """
    pass


def downgrade():
    """Placeholder downgrade: no operations."""
    pass
