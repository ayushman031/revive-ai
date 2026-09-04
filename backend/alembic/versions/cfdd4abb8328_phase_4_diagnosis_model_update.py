"""phase 4 diagnosis model update

Revision ID: cfdd4abb8328
Revises: 35ec28ef0506
Create Date: 2026-09-04 19:42:48.224070

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'cfdd4abb8328'
down_revision: Union[str, Sequence[str], None] = '35ec28ef0506'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('diagnoses', sa.Column('payment_attempt_id', sa.UUID(), nullable=False))
    op.add_column('diagnoses', sa.Column('evidence', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False))
    op.create_foreign_key('fk_diagnoses_payment_attempt_id', 'diagnoses', 'payment_attempts', ['payment_attempt_id'], ['id'])
    op.create_index(op.f('ix_diagnoses_payment_attempt_id'), 'diagnoses', ['payment_attempt_id'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_diagnoses_payment_attempt_id'), table_name='diagnoses')
    op.drop_constraint('fk_diagnoses_payment_attempt_id', 'diagnoses', type_='foreignkey')
    op.drop_column('diagnoses', 'evidence')
    op.drop_column('diagnoses', 'payment_attempt_id')

