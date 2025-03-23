import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base

load_dotenv()
engine = create_engine(f"{os.getenv('DB_DRIVER')}:///{os.getenv('DB_NAME')}",
                       pool_size=20,  # Основной размер пула
                       max_overflow=20,  # Максимальное количество дополнительных соединений
                       pool_timeout=60,  # Время ожидания перед тайм-аутом
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
