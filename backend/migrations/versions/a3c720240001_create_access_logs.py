"""Create privacy-limited audit events and durable workflow admission records."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'a3c720240001'
down_revision = '55e064ea8ca4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'access_logs',
        sa.Column('id', postgresql.UUID(), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.Text(), nullable=True),
        sa.Column('action', sa.Text(), nullable=False),
        sa.Column('resource_type', sa.Text(), nullable=True),
        sa.Column('resource_id', sa.Text(), nullable=True),
        sa.Column('outcome', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('idx_access_logs_user_action_created', 'access_logs', ['user_id', 'action', 'created_at'])


def downgrade():
    op.drop_index('idx_access_logs_user_action_created', table_name='access_logs')
    op.drop_table('access_logs')
