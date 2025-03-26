import re

from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, declared_attr
from sqlalchemy import Integer, DateTime, func


class Base(AsyncAttrs, DeclarativeBase):

    @declared_attr.directive
    def __tablename__(self) -> str:
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', self.__name__).lower()
        if not name.endswith('s'):
            name += 's'
        return name


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        server_default=None,
        onupdate=func.now(),
        nullable=True
    )


class IdMixin:
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        index=True
    )


class BaseModel(IdMixin, TimestampMixin, Base):
    __abstract__ = True
