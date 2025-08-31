from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import UserRole
from app.models import Course, Group, User
from app.repositories import CourseRepository, GroupRepository


class GuestService:
    def __init__(self, session: AsyncSession,
                 course_repo: CourseRepository,
                 group_repo: GroupRepository) -> None:
        self._session = session
        self._course_repo = course_repo
        self._group_repo = group_repo

    async def get_all_courses(self) -> Sequence[Course]:
        return await self._course_repo.list_all()

    async def get_course_groups(self, course_id: int) -> Sequence[Group]:
        return await self._group_repo.get_by_course_id(course_id)

    async def register_user(self, user: User, group_id: int) -> User:
        user.group_id = group_id
        user.role = UserRole.USER
        await self._session.commit()
        await self._session.refresh(user)
        return user
