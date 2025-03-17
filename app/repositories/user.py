from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database.enums import Role
from app.database.models import User, Group


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, user_id: int, username: str = None, name: str = None,
               role: Role = Role.USER, group_id: int = None) -> User:
        user = User(user_id=user_id, username=username, name=name,
                    role=role, group_id=group_id)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def get_by_user_id(self, user_id: int) -> User | None:
        query = select(User).where(User.user_id == user_id)
        result = self.session.execute(query)
        return result.scalars().first()

    def get_with_group(self, user_id: int) -> User | None:
        query = select(User).options(selectinload(User.group)).where(User.user_id == user_id)
        result = self.session.execute(query)
        return result.scalars().first()

    def get_all(self) -> list[User]:
        query = select(User)
        result = self.session.execute(query)
        return list(result.scalars().all())

    def get_by_group(self, group_name: str) -> list[User]:
        query = select(User).join(User.group).where(Group.name == group_name)
        result = self.session.execute(query)
        return list(result.scalars().all())

    def get_by_role(self, role: Role) -> list[User]:
        query = select(User).where(User.role == role)
        result = self.session.execute(query)
        return list(result.scalars().all())

    def update(self, user: User) -> User:
        self.session.commit()
        self.session.refresh(user)
        return user

    def delete(self, user: User) -> None:
        self.session.delete(user)
        self.session.commit()