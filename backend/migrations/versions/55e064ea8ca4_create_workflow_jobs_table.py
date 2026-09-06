"""create workflow jobs table

Revision ID: 55e064ea8ca4
Revises: 
Create Date: 2026-09-05 12:20:45.082524

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '55e064ea8ca4'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'workflow_jobs',
        sa.Column('id', postgresql.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.Text(), nullable=False),
        sa.Column('target_role', sa.Text(), nullable=True),
        sa.Column('job_description', sa.Text(), nullable=False),
        sa.Column('cv_object_path', sa.Text(), nullable=True),
        sa.Column('status', sa.Text(), server_default=sa.text("'queued'"), nullable=False),
        sa.Column('result', postgresql.JSONB(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.CheckConstraint(
            "status IN ('queued', 'processing', 'completed', 'failed')",
            name='ck_workflow_jobs_status',
        ),
    )
    op.create_index('idx_workflow_jobs_user', 'workflow_jobs', ['user_id'])
    op.create_index('idx_workflow_jobs_status', 'workflow_jobs', ['status'])
    op.create_index('idx_workflow_jobs_created_at', 'workflow_jobs', ['created_at'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_workflow_jobs_created_at', table_name='workflow_jobs')
    op.drop_index('idx_workflow_jobs_status', table_name='workflow_jobs')
    op.drop_index('idx_workflow_jobs_user', table_name='workflow_jobs')
    op.drop_table('workflow_jobs')
