"""Agricultural Knowledge Library Pydantic v2 schemas."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class KnowledgeArticleResponse(BaseModel):
    id: str
    cropType: str
    category: str
    titleBn: str
    titleEn: Optional[str] = None
    summaryBn: str
    contentBn: str
    recommendedPracticesBn: Optional[str] = None
    version: int
    publishedAt: datetime
    updatedAt: datetime

    model_config = ConfigDict(from_attributes=True)


class KnowledgeCatalogResponse(BaseModel):
    articles: List[KnowledgeArticleResponse]
    totalCount: int
    latestVersion: int
    syncedAt: datetime
