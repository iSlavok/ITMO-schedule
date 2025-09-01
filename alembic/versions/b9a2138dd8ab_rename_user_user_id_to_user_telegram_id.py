"""rename User.user_id to User.telegram_id

Revision ID: b9a2138dd8ab
Revises: 
Create Date: 2025-09-01 11:52:05.526180

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import reflection

# revision identifiers, used by Alembic.
revision: str = 'b9a2138dd8ab'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()

    op.add_column('logs', sa.Column('temp_user_id', sa.Integer(), nullable=True))
    op.add_column('ratings', sa.Column('temp_user_id', sa.Integer(), nullable=True))

    conn.execute(sa.text('''
                         UPDATE logs l
                         SET temp_user_id = u.id
                         FROM users u
                         WHERE l.user_id = u.user_id
                         '''))

    conn.execute(sa.text('''
                         UPDATE ratings r
                         SET temp_user_id = u.id
                         FROM users u
                         WHERE r.user_id = u.user_id
                         '''))

    op.drop_constraint('logs_user_id_fkey', 'logs', type_='foreignkey')
    op.drop_constraint('ratings_user_id_fkey', 'ratings', type_='foreignkey')

    conn.execute(sa.text('UPDATE logs SET user_id = temp_user_id'))
    conn.execute(sa.text('UPDATE ratings SET user_id = temp_user_id'))

    op.create_foreign_key(None, 'logs', 'users', ['user_id'], ['id'])
    op.create_foreign_key(None, 'ratings', 'users', ['user_id'], ['id'])

    op.drop_column('logs', 'temp_user_id')
    op.drop_column('ratings', 'temp_user_id')

    op.add_column('users', sa.Column('telegram_id', sa.BigInteger(), nullable=True))
    conn.execute(sa.text('UPDATE users SET telegram_id = user_id'))
    op.alter_column('users', 'telegram_id', nullable=False)

    op.create_index(op.f('ix_users_telegram_id'), 'users', ['telegram_id'], unique=True)

    op.drop_index('ix_users_user_id', table_name='users')
    op.drop_column('users', 'user_id')

    op.create_index(op.f('ix_groups_name'), 'groups', ['name'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()

    op.drop_index(op.f('ix_groups_name'), table_name='groups')

    op.add_column('logs', sa.Column('temp_user_id', sa.BigInteger(), nullable=True))
    op.add_column('ratings', sa.Column('temp_user_id', sa.BigInteger(), nullable=True))

    conn.execute(sa.text('''
                         UPDATE logs l
                         SET temp_user_id = u.telegram_id
                         FROM users u
                         WHERE l.user_id = u.id
                         '''))

    conn.execute(sa.text('''
                         UPDATE ratings r
                         SET temp_user_id = u.telegram_id
                         FROM users u
                         WHERE r.user_id = u.id
                         '''))

    op.add_column('users', sa.Column('user_id', sa.BIGINT(), nullable=True))
    conn.execute(sa.text('UPDATE users SET user_id = telegram_id'))
    op.alter_column('users', 'user_id', nullable=False)
    op.create_index('ix_users_user_id', 'users', ['user_id'], unique=True)

    insp = reflection.Inspector.from_engine(conn)
    for fk in insp.get_foreign_keys('logs'):
        if fk['referred_columns'] == ['id']:
            op.drop_constraint(fk['name'], 'logs', type_='foreignkey')

    for fk in insp.get_foreign_keys('ratings'):
        if fk['referred_columns'] == ['id']:
            op.drop_constraint(fk['name'], 'ratings', type_='foreignkey')

    conn.execute(sa.text('UPDATE logs SET user_id = temp_user_id'))
    conn.execute(sa.text('UPDATE ratings SET user_id = temp_user_id'))

    op.create_foreign_key('logs_user_id_fkey', 'logs', 'users', ['user_id'], ['user_id'])
    op.create_foreign_key('ratings_user_id_fkey', 'ratings', 'users', ['user_id'], ['user_id'])

    op.drop_column('logs', 'temp_user_id')
    op.drop_column('ratings', 'temp_user_id')

    op.drop_index(op.f('ix_users_telegram_id'), table_name='users')
    op.drop_column('users', 'telegram_id')