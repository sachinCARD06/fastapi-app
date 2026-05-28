"""change user id to prefixed ulid

Revision ID: 62f2ce7ed53f
Revises: 868ec7f4e4f2
Create Date: 2026-05-26 18:05:50.020082

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '62f2ce7ed53f'
down_revision: Union[str, None] = '868ec7f4e4f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop FK constraints that reference users.id before changing its type.
    #    PostgreSQL auto-names these as <table>_<col>_fkey when no name is given.
    op.drop_constraint('hospitals_created_by_fkey', 'hospitals', type_='foreignkey')
    op.drop_constraint('hospitals_updated_by_fkey', 'hospitals', type_='foreignkey')

    # 2. Drop the serial default on users.id (it was an autoincrement integer).
    op.execute("ALTER TABLE users ALTER COLUMN id DROP DEFAULT")

    # 3. Change column types using USING casts (required by PostgreSQL for int→varchar).
    op.execute("ALTER TABLE users ALTER COLUMN id TYPE VARCHAR(32) USING id::text")
    op.execute("ALTER TABLE hospitals ALTER COLUMN id TYPE VARCHAR(32) USING id::text")
    op.execute("ALTER TABLE hospitals ALTER COLUMN created_by TYPE VARCHAR(32) USING created_by::text")
    op.execute("ALTER TABLE hospitals ALTER COLUMN updated_by TYPE VARCHAR(32) USING updated_by::text")

    # 4. Recreate FK constraints with the same names.
    op.create_foreign_key(
        'hospitals_created_by_fkey', 'hospitals', 'users', ['created_by'], ['id']
    )
    op.create_foreign_key(
        'hospitals_updated_by_fkey', 'hospitals', 'users', ['updated_by'], ['id']
    )


def downgrade() -> None:
    op.drop_constraint('hospitals_created_by_fkey', 'hospitals', type_='foreignkey')
    op.drop_constraint('hospitals_updated_by_fkey', 'hospitals', type_='foreignkey')

    op.execute("ALTER TABLE hospitals ALTER COLUMN updated_by TYPE INTEGER USING updated_by::integer")
    op.execute("ALTER TABLE hospitals ALTER COLUMN created_by TYPE INTEGER USING created_by::integer")
    op.execute("ALTER TABLE hospitals ALTER COLUMN id TYPE INTEGER USING id::integer")
    op.execute("ALTER TABLE users ALTER COLUMN id TYPE INTEGER USING id::integer")

    # Restore serial default for users.id
    op.execute("CREATE SEQUENCE IF NOT EXISTS users_id_seq OWNED BY users.id")
    op.execute("ALTER TABLE users ALTER COLUMN id SET DEFAULT nextval('users_id_seq')")

    op.create_foreign_key(
        'hospitals_created_by_fkey', 'hospitals', 'users', ['created_by'], ['id']
    )
    op.create_foreign_key(
        'hospitals_updated_by_fkey', 'hospitals', 'users', ['updated_by'], ['id']
    )
