from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import env_config
from app.database import Base

database_url = URL.create(
    drivername=env_config.DB_DRIVER,
    host=env_config.DB_HOST,
    port=env_config.DB_PORT,
    username=env_config.DB_USER,
    password=env_config.DB_PASS.get_secret_value(),
    database=env_config.DB_NAME,
)

async_engine = create_async_engine(
    database_url,
    echo=False,
    future=True,
    pool_size=env_config.DB_POOL_SIZE,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession]:
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    await async_engine.dispose()
