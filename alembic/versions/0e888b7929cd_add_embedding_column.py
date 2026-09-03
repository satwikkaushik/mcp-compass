# alembic/versions/0e888b7929cd_add_embedding_column.py
"""add embedding column

Revision ID: 0e888b7929cd
Revises: ad6ab59e8d46
Create Date: 2026-09-03 21:32:31.383641

"""

from collections.abc import Sequence

import pgvector.sqlalchemy
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0e888b7929cd"
down_revision: str | Sequence[str] | None = "ad6ab59e8d46"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column(
        "mcp_servers",
        sa.Column("embedding", pgvector.sqlalchemy.Vector(dim=384), nullable=True),
    )
    op.execute(
        "CREATE INDEX mcp_servers_embedding_hnsw_idx ON mcp_servers "
        "USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS mcp_servers_embedding_hnsw_idx")
    op.drop_column("mcp_servers", "embedding")
    op.execute("DROP EXTENSION IF EXISTS vector")
