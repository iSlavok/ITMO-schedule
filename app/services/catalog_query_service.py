from collections.abc import Sequence

from app.models import Course, Faculty, Group
from app.repositories import CourseRepository, FacultyRepository, GroupRepository


class CatalogQueryService:
    """Reads the catalog for the group picker.

    The writing half lives in CatalogService, which runs on the update loop and
    owns its own session. This one is per-request, so it takes the session the
    middleware already opened.
    """

    def __init__(self,
                 course_repo: CourseRepository,
                 group_repo: GroupRepository,
                 faculty_repo: FacultyRepository) -> None:
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
