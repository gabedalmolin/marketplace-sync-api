import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings


@pytest.fixture(scope="session", autouse=True)
def require_integration_opt_in() -> None:
    if os.getenv("RUN_INTEGRATION_TESTS") != "1":
        pytest.skip("set RUN_INTEGRATION_TESTS=1 to run PostgreSQL integration tests")


@pytest_asyncio.fixture
async def database_session() -> AsyncIterator[AsyncSession]:
    settings = get_settings()
    database_url = str(settings.database_url)
    parsed_url = make_url(database_url)

    if settings.app_env == "production":
        pytest.fail("integration tests cannot run in the production environment")

    if parsed_url.host not in {"localhost", "127.0.0.1"}:
        pytest.fail("integration tests require a local PostgreSQL database")

    engine = create_async_engine(
        database_url,
        poolclass=NullPool,
    )

    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()

            try:
                async with AsyncSession(
                    bind=connection,
                    expire_on_commit=False,
                ) as session:
                    yield session
            finally:
                if transaction.is_active:
                    await transaction.rollback()
    finally:
        await engine.dispose()
