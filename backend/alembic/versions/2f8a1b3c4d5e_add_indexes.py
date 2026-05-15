"""add_indexes

Revision ID: 2f8a1b3c4d5e
Revises: 0b4962a1f055
Create Date: 2026-05-15 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2f8a1b3c4d5e'
down_revision: Union[str, None] = '0b4962a1f055'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. submissions: index on (student_id, assignment_id, problem_id) - used heavily in grade calculation
    op.create_index(
        'idx_submissions_student_assign_prob',
        'submissions',
        ['student_id', 'assignment_id', 'problem_id'],
        unique=False,
        postgresql_using='btree',
        sqlite_where=None,
    )

    # 2. submissions: index on (assignment_id, status) - used for submission queries
    op.create_index(
        'idx_submissions_assign_status',
        'submissions',
        ['assignment_id', 'status'],
        unique=False,
        postgresql_using='btree',
        sqlite_where=None,
    )

    # 3. assignment_problems: index on (assignment_id, problem_id) - used in joins
    op.create_index(
        'idx_assign_problems_assign_prob',
        'assignment_problems',
        ['assignment_id', 'problem_id'],
        unique=False,
        postgresql_using='btree',
        sqlite_where=None,
    )

    # 4. problem_function_signatures: index on (problem_id, language) - used for fetching templates
    op.create_index(
        'idx_prob_func_sig_prob_lang',
        'problem_function_signatures',
        ['problem_id', 'language'],
        unique=False,
        postgresql_using='btree',
        sqlite_where=None,
    )


def downgrade() -> None:
    op.drop_index('idx_submissions_student_assign_prob', table_name='submissions')
    op.drop_index('idx_submissions_assign_status', table_name='submissions')
    op.drop_index('idx_assign_problems_assign_prob', table_name='assignment_problems')
    op.drop_index('idx_prob_func_sig_prob_lang', table_name='problem_function_signatures')
