"""Pytest fixtures with async in-memory SQLite test database."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.session import get_db_session
from app.main import app as fastapi_app

# Import models so they are registered with Base metadata
from app.modules.users import models as user_models  # noqa: F401
from app.modules.auth import models as auth_models  # noqa: F401
from app.modules.crop_assistant import models as crop_models  # noqa: F401
from app.modules.equipment import models as equipment_models  # noqa: F401
from app.modules.rentals import models as rental_models  # noqa: F401
from app.modules.crop_marketplace import models as crop_marketplace_models  # noqa: F401
from app.modules.messaging import models as messaging_models  # noqa: F401
from app.modules.knowledge import models as knowledge_models  # noqa: F401
from app.modules.sync import models as sync_models  # noqa: F401
from app.modules.admin import models as admin_models  # noqa: F401
from app.modules.pilot import models as pilot_models  # noqa: F401
from app.modules.jobs import models as job_models  # noqa: F401
from app.modules.notifications import models as notification_models  # noqa: F401

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def test_db():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def client(test_db: AsyncSession):
    from unittest.mock import patch
    from app.core.config import settings

    async def override_db():
        yield test_db

    fastapi_app.dependency_overrides[get_db_session] = override_db

    with patch.object(settings, "DATABASE_BACKEND", "sqlite"):
        async with AsyncClient(
            transport=ASGITransport(app=fastapi_app),
            base_url="http://testserver",
        ) as ac:
            yield ac

    fastapi_app.dependency_overrides.clear()

