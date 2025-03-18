from sqlalchemy import select
from sqlalchemy.orm import selectinload, Session

from app.database import Group, Course


class GroupRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, name: str, course_id: int) -> Group:
        group = Group(name=name, course_id=course_id)
        self.session.add(group)
        self.session.commit()
        self.session.refresh(group)
        return group

    def get_by_name(self, name: str) -> Group | None:
        query = select(Group).where(Group.name == name)
        result = self.session.execute(query)
        return result.scalars().first()

    def get_by_id(self, group_id):
        query = select(Group).where(Group.id == group_id)
        result = self.session.execute(query)
        return result.scalars().first()

    def get_with_users(self, name: str) -> Group | None:
        query = select(Group).options(selectinload(Group.users)).where(Group.name == name)
        result = self.session.execute(query)
        return result.scalars().first()

    def get_with_course(self, name: str) -> Group | None:
        query = select(Group).options(selectinload(Group.course)).where(Group.name == name)
        result = self.session.execute(query)
        return result.scalars().first()

    def get_all(self) -> list[Group]:
        query = select(Group)
        result = self.session.execute(query)
        return list(result.scalars().all())

    def get_by_course_name(self, course_name: str) -> list[Group]:
        query = select(Group).join(Group.course).where(Course.name == course_name)
        result = self.session.execute(query)
        return list(result.scalars().all())

    def get_by_course_id(self, course_id: int) -> list[Group]:
        query = select(Group).where(Group.course_id == course_id)
        result = self.session.execute(query)
        return list(result.scalars().all())

    def update(self, group: Group) -> Group:
        self.session.commit()
        self.session.refresh(group)
        return group

    def delete(self, group: Group) -> None:
        self.session.delete(group)
        self.session.commit()
