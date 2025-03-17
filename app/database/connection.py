# from contextlib import asynccontextmanager
#
# from sqlalchemy import text, NullPool
# from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
# from typing import AsyncGenerator
# from dotenv import load_dotenv
# import os
#
# load_dotenv()
# engine = create_async_engine(
#     f"{os.getenv('DB_DRIVER')}:///{os.getenv('DB_NAME')}",
#     echo=False,
#     connect_args={"check_same_thread": False},
#     pool_pre_ping=True,
# )
#
# async_session_factory = async_sessionmaker(
#     engine,
#     expire_on_commit=False,
#     class_=AsyncSession
# )
#
#
# @asynccontextmanager
# async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
#     session = async_session_factory()
#     try:
#         print("Opening session")
#         yield session
#     finally:
#         print("Closing session")
#         await session.close()
#
#
# async def init_db():
#     from .base import Base
#
#     async with engine.begin() as conn:
#         # from .models import user
#         await conn.run_sync(lambda sync_conn: sync_conn.execute(text("PRAGMA foreign_keys=ON")))
#         await conn.run_sync(Base.metadata.create_all)
#
#
# async def close_db():
#     await engine.dispose()
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base

load_dotenv()
engine = create_engine(f"{os.getenv('DB_DRIVER')}:///{os.getenv('DB_NAME')}")
Session = sessionmaker(bind=engine)


def get_session() -> Session:
    session = Session()
    try:
        yield session
    finally:
        session.close()


def init_db():
    Base.metadata.create_all(bind=engine)
