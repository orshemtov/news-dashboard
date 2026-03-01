"""add hnsw index on embedding column

Revision ID: 784a577dd6ae
Revises: 151c3531d96a
Create Date: 2026-03-01 13:20:18.914242

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "784a577dd6ae"
down_revision: Union[str, Sequence[str], None] = "151c3531d96a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add HNSW index on embedding column for fast cosine similarity search."""
    op.execute(
        """
        CREATE INDEX ix_articles_embedding_hnsw
        ON articles
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )


def downgrade() -> None:
    """Drop HNSW index."""
    op.drop_index("ix_articles_embedding_hnsw", table_name="articles")
