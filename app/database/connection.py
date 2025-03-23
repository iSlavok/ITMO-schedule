import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base

load_dotenv()
engine = create_engine(f"{os.getenv('DB_DRIVER')}:///{os.getenv('DB_NAME')}",
                       pool_size=20,
                       max_overflow=20,
                       pool_timeout=60,
                       )
Session = sessionmaker(bind=engine)


def get_session() -> Session:
    session = Session()
    try:
        yield session
    finally:
        session.close()


def init_db():
    Base.metadata.create_all(bind=engine)
