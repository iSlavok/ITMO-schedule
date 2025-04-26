from typing import AsyncGenerator

from sqlalchemy import URL
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from bot.config import env_config

database_url = URL.create(
    drivername=env_config.DB_DRIVER,
    host=env_config.DB_HOST,
    port=env_config.DB_PORT,
    username=env_config.DB_USER,
    password=env_config.DB_PASS,
    database=env_config.DB_NAME,
)

async_engine = create_async_engine(
    database_url,
    echo=False,
    future=True
)

async_session_factory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e


async def init_db():
    from bot.database import Base
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
