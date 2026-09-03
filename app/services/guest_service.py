from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import UserRole
from app.models import Course, Faculty, Group, User
from app.repositories import CourseRepository, FacultyRepository, GroupRepository


class GuestService:
    def __init__(self, session: AsyncSession,
                 course_repo: CourseRepository,
                 group_repo: GroupRepository,
                 faculty_repo: FacultyRepository) -> None:
        self._session = session
        self._course_repo = course_repo
        self._group_repo = group_repo
        self._faculty_repo = faculty_repo

    async def get_all_faculties(self) -> Sequence[Faculty]:
        return await self._faculty_repo.list_all()

    async def get_faculty_courses(self, faculty_id: int) -> Sequence[Course]:
        """Only the courses this faculty actually has groups on."""
        return await self._course_repo.get_by_faculty_id(faculty_id)

    async def get_course_groups(self, course_id: int, faculty_id: int) -> Sequence[Group]:
        return await self._group_repo.get_by_course_and_faculty(course_id, faculty_id)

    async def register_user(self, user: User, group_id: int) -> User:
        user.group_id = group_id
        user.role = UserRole.USER
        await self._session.commit()
        await self._session.refresh(user)
        return user
