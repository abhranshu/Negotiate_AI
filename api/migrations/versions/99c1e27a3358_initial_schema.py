"""initial schema: users, cases, documents, messages

Revision ID: 99c1e27a3358
Revises:
Create Date: 2026-09-06 22:02:45.567205

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '99c1e27a3358'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the initial schema: users, cases, documents, messages."""
    # ── users ───────────────────────────────────────────────────────────────
    op.create_table(
        'users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False, server_default='claimant'),
        sa.Column('company_name', sa.String(), nullable=True),
        sa.Column('udyam_number', sa.String(), nullable=True),
        sa.Column('gstin', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # ── cases ──────────────────────────────────────────────────────────────
    op.create_table(
        'cases',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('case_number', sa.String(), nullable=True),
        sa.Column('claimant_id', sa.String(), nullable=False),
        sa.Column('respondent_id', sa.String(), nullable=True),
        sa.Column('dispute_type', sa.String(), nullable=True),
        sa.Column('claim_amount', sa.Float(), nullable=True),
        sa.Column('overdue_days', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('state', sa.String(), nullable=True),
        sa.Column('industry', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True, server_default='draft'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('doc_gap_analysis', sa.JSON(), nullable=True),
        sa.Column('case_summary_text', sa.Text(), nullable=True),
        sa.Column('case_strength', sa.String(), nullable=True),
        sa.Column('settlement_probability', sa.Float(), nullable=True),
        sa.Column('settlement_range_low', sa.Float(), nullable=True),
        sa.Column('settlement_range_high', sa.Float(), nullable=True),
        sa.Column('adjudication_days', sa.Integer(), nullable=True),
        sa.Column('prediction_confidence', sa.String(), nullable=True),
        sa.Column('prediction_recommendation', sa.Text(), nullable=True),
        sa.Column('agreement_text', sa.Text(), nullable=True),
        sa.Column('agreement_amount', sa.Float(), nullable=True),
        sa.Column('agreement_valid', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['claimant_id'], ['users.id'], name=op.f('cases_claimant_id_fkey')),
        sa.ForeignKeyConstraint(['respondent_id'], ['users.id'], name=op.f('cases_respondent_id_fkey')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_cases_case_number'), 'cases', ['case_number'], unique=True)
    op.create_index(op.f('ix_cases_claimant_id'), 'cases', ['claimant_id'], unique=False)
    op.create_index(op.f('ix_cases_respondent_id'), 'cases', ['respondent_id'], unique=False)
    op.create_index(op.f('ix_cases_status'), 'cases', ['status'], unique=False)

    # ── documents ──────────────────────────────────────────────────────────
    op.create_table(
        'documents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('case_id', sa.String(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('file_size_kb', sa.Integer(), nullable=True),
        sa.Column('doc_type', sa.String(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('extracted_text', sa.Text(), nullable=True),
        sa.Column('key_fields', sa.JSON(), nullable=True),
        sa.Column('is_valid', sa.Boolean(), nullable=True),
        sa.Column('issues', sa.JSON(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], name=op.f('documents_case_id_fkey'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_documents_case_id'), 'documents', ['case_id'], unique=False)

    # ── messages ───────────────────────────────────────────────────────────
    op.create_table(
        'messages',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('case_id', sa.String(), nullable=False),
        sa.Column('party', sa.String(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('language', sa.String(), nullable=True),
        sa.Column('offer', sa.Float(), nullable=True),
        sa.Column('sentiment', sa.String(), nullable=True),
        sa.Column('phase', sa.String(), nullable=True),
        sa.Column('round_num', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], name=op.f('messages_case_id_fkey'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_messages_case_id'), 'messages', ['case_id'], unique=False)


def downgrade() -> None:
    """Drop all tables in reverse dependency order."""
    op.drop_table('messages')
    op.drop_table('documents')
    op.drop_index(op.f('ix_cases_status'), table_name='cases')
    op.drop_index(op.f('ix_cases_respondent_id'), table_name='cases')
    op.drop_index(op.f('ix_cases_claimant_id'), table_name='cases')
    op.drop_index(op.f('ix_cases_case_number'), table_name='cases')
    op.drop_table('cases')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
