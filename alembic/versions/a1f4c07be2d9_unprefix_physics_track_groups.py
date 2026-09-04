"""drop the stray prefix from physics track groups

Revision ID: a1f4c07be2d9
Revises: c4b18f7a2d51
Create Date: 2026-09-04

c4b18f7a2d51 prefixed every physics group at once, but senior years are taught
in tracks that go by name rather than by number, so the letter landed in front
of a word: "Zрадио", "Zнавигация Z3300". The parser now prefixes numbers only,
so those names lose the letter here to match. Names are rewritten in place,
which leaves the users attached to them where they are.
"""
from collections.abc import Sequence
from typing import Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a1f4c07be2d9'
down_revision: Union[str, None] = 'c4b18f7a2d51'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PHYSICS = "(SELECT id FROM faculties WHERE code = 'PHYSICS')"


def upgrade() -> None:
    # "Z" before a digit is the prefix of a group number and stays
    op.execute(
        "UPDATE groups SET name = substring(name from 2) "
        f"WHERE faculty_id = {PHYSICS} AND name ~ '^Z[^0-9]'",
    )


def downgrade() -> None:
    op.execute(
        "UPDATE groups SET name = 'Z' || name "
        f"WHERE faculty_id = {PHYSICS} AND name NOT LIKE 'Z%'",
    )
