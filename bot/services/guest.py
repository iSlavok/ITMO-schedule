from sqlalchemy.ext.asyncio import AsyncSession

from bot.enums import UserRole
from bot.models import User
from bot.repositories import CourseRepository, GroupRepository, UserRepository


class GuestService:
    def __init__(self, session: AsyncSession, course_repo: CourseRepository, group_repo: GroupRepository):
        self._session = session
        self._course_repo = course_repo
        self._group_repo = group_repo

    async def get_all_courses(self):
        return await self._course_repo.list_all()

    async def get_course_groups(self, course_id: int):
        return await self._group_repo.get_by_course_id(course_id)

    async def register_user(self, user: User, group_id: int) -> User:
        user.group_id = group_id
        user.role = UserRole.USER
        await self._session.commit()
        await self._session.refresh(user)
        return user
