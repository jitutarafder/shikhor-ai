"""Agricultural Knowledge Library database models.

Strictly complies with:
- AGENTS.md Rule 19: Reviewed agricultural knowledge.
- AGENTS.md Rule 23: Bangla-first content.
"""

from datetime import datetime, timezone
import uuid
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class KnowledgeArticle(Base):
    __tablename__ = "knowledge_articles"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    crop_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, comment="e.g. paddy, potato, wheat, mustard"
    )
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, comment="e.g. pest, disease, fertilizer, irrigation"
    )
    title_bn: Mapped[str] = mapped_column(String(200), nullable=False)
    title_en: Mapped[str] = mapped_column(String(200), nullable=True)
    summary_bn: Mapped[str] = mapped_column(Text, nullable=False)
    content_bn: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_practices_bn: Mapped[str] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
