"""Agricultural Knowledge Library API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.modules.knowledge.schemas import KnowledgeCatalogResponse
from app.modules.knowledge.service import get_knowledge_catalog, seed_default_knowledge

router = APIRouter(prefix="/knowledge", tags=["Knowledge Library"])


@router.get("", response_model=KnowledgeCatalogResponse, status_code=status.HTTP_200_OK)
async def list_knowledge(
    crop_type: Optional[str] = Query(None, description="Filter by crop (e.g. paddy, potato)"),
    category: Optional[str] = Query(None, description="Filter by category (disease, irrigation, etc.)"),
    since_version: Optional[int] = Query(None, description="Incremental sync: only articles newer than version"),
    db: AsyncSession = Depends(get_db_session),
) -> KnowledgeCatalogResponse:
    """Lists verified agricultural knowledge articles with version tracking for offline cache."""
    # Ensure initial seeds exist
    await seed_default_knowledge(db)
    return await get_knowledge_catalog(
        db=db,
        crop_type=crop_type,
        category=category,
        since_version=since_version,
    )
