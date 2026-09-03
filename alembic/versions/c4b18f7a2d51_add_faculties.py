"""add faculties, prefix physics groups, seed CT groups

Revision ID: c4b18f7a2d51
Revises: 2ca54a9f1cfb
Create Date: 2026-09-02

Groups and lecturers become faculty-scoped. Existing rows are all from the
physics faculty, so they are backfilled with it and its group numbers get the
"Z" prefix the parser now emits. CT groups are seeded here as well, to give
registration something to offer before the first parse of the new sheet lands;
from then on the catalog sync keeps both faculties up to date.
"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c4b18f7a2d51'
down_revision: Union[str, None] = '2ca54a9f1cfb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# SQLAlchemy stores an Enum column by member name, as it already does for user roles
FACULTIES = [
    ("PHYSICS", "ФизФак"),
    ("CT", "КТ"),
]
CT_GROUPS = {
    "1 курс": ["M3132", "M3133", "M3134", "M3135", "M3136", "M3137", "M3138",
               "M3139", "M3141", "M3142", "M3147", "M3148", "M3149"],
    "2 курс": ["M3232", "M3233", "M3234", "M3235", "M3236", "M3237", "M3238",
               "M3239", "M3241", "M3242", "M3247", "M3248", "M3249"],
    "3 курс": ["M3332", "M3333", "M3334", "M3335", "M3336", "M3337", "M3338",
               "M3339", "M3341", "M3342"],
    "4 курс": ["M3432", "M3433", "M3434", "M3435", "M3436", "M3437", "M3438", "M3439"],
}


def upgrade() -> None:
    op.create_table(
        "faculties",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "code",
            sa.Enum(*[code for code, _ in FACULTIES], name="faculty_code_enum",
                    native_enum=False, create_constraint=True),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_faculties_id"), "faculties", ["id"])
    op.create_index(op.f("ix_faculties_code"), "faculties", ["code"], unique=True)
    op.create_unique_constraint("uq_faculties_name", "faculties", ["name"])

    for code, name in FACULTIES:
        op.execute(
            sa.text("INSERT INTO faculties (code, name) VALUES (:code, :name)")
            .bindparams(code=code, name=name),
        )

    _add_faculty_column("groups")
    _add_faculty_column("lecturers")

    # server defaults only fill the existing rows; the models set both in Python
    op.add_column("groups", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("lecturers", sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_unique_constraint("uq_lecturer_name_faculty", "lecturers", ["name", "faculty_id"])

    # the sheet writes "Z" on some groups and omits it on others; the parser always emits it.
    # prefixing before the unique constraint, so a collision fails here instead of passing silently
    op.execute("UPDATE groups SET name = 'Z' || name WHERE name NOT LIKE 'Z%'")
    op.create_unique_constraint("uq_group_name_faculty", "groups", ["name", "faculty_id"])

    for course_name, groups in CT_GROUPS.items():
        op.execute(
            sa.text("INSERT INTO courses (name) SELECT :course "
                    "WHERE NOT EXISTS (SELECT 1 FROM courses WHERE name = :course)")
            .bindparams(course=course_name),
        )
        for group_name in groups:
            op.execute(
                sa.text(
                    "INSERT INTO groups (name, course_id, faculty_id) "
                    "SELECT :group, c.id, f.id FROM courses c, faculties f "
                    "WHERE c.name = :course AND f.code = 'CT' "
                    "AND NOT EXISTS ("
                    "    SELECT 1 FROM groups g WHERE g.name = :group AND g.faculty_id = f.id"
                    ")",
                ).bindparams(group=group_name, course=course_name),
            )

    op.execute("ALTER TABLE groups ALTER COLUMN is_active DROP DEFAULT")
    op.execute("ALTER TABLE lecturers ALTER COLUMN is_hidden DROP DEFAULT")


def downgrade() -> None:
    op.execute("DELETE FROM groups WHERE faculty_id = (SELECT id FROM faculties WHERE code = 'CT')")
    op.execute("DELETE FROM lecturers WHERE faculty_id = (SELECT id FROM faculties WHERE code = 'CT')")
    op.execute("UPDATE groups SET name = substring(name from 2) WHERE name LIKE 'Z%'")

    op.drop_constraint("uq_group_name_faculty", "groups", type_="unique")
    op.drop_constraint("uq_lecturer_name_faculty", "lecturers", type_="unique")
    op.drop_column("lecturers", "is_hidden")
    op.drop_column("groups", "is_active")
    _drop_faculty_column("lecturers")
    _drop_faculty_column("groups")

    op.drop_constraint("uq_faculties_name", "faculties", type_="unique")
    op.drop_index(op.f("ix_faculties_code"), table_name="faculties")
    op.drop_index(op.f("ix_faculties_id"), table_name="faculties")
    op.drop_table("faculties")


def _add_faculty_column(table: str) -> None:
    """Attach a table to the physics faculty: every existing row predates the split."""
    op.add_column(table, sa.Column("faculty_id", sa.Integer(), nullable=True))
    op.execute(f"UPDATE {table} SET faculty_id = (SELECT id FROM faculties WHERE code = 'PHYSICS')")  # noqa: S608
    op.alter_column(table, "faculty_id", nullable=False)
    op.create_index(op.f(f"ix_{table}_faculty_id"), table, ["faculty_id"])
    op.create_foreign_key(f"fk_{table}_faculty_id", table, "faculties", ["faculty_id"], ["id"])


def _drop_faculty_column(table: str) -> None:
    op.drop_constraint(f"fk_{table}_faculty_id", table, type_="foreignkey")
    op.drop_index(op.f(f"ix_{table}_faculty_id"), table_name=table)
    op.drop_column(table, "faculty_id")
