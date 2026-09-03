from dataclasses import dataclass

from loguru import logger

from app.database import get_session
from app.enums import FacultyCode
from app.models import Group
from app.repositories import CourseRepository, FacultyRepository, GroupRepository, LecturerRepository
from app.schemas import Schedule


@dataclass
class SyncReport:
    courses: int = 0
    groups: int = 0
    deactivated_groups: int = 0
    lecturers: int = 0

    def __bool__(self) -> bool:
        return bool(self.courses or self.groups or self.deactivated_groups or self.lecturers)


class CatalogService:
    """Keeps courses, groups and lecturers in step with the parsed schedules.

    The sheet is the source of truth for what exists, so rows are created from it
    instead of by hand. Nothing is deleted: users are attached to groups and
    ratings to lecturers. A group that leaves the sheet is deactivated instead,
    which only takes it out of registration.
    """

    async def sync_from_schedule(self, faculty: FacultyCode, schedule: Schedule) -> SyncReport:
        report = SyncReport()

        async with get_session() as session:
            faculty_row = await FacultyRepository(session).get_by_code(faculty)
            if faculty_row is None:
                logger.warning(f"Faculty {faculty.value} is missing, skipping the catalog sync")
                return report

            course_repository = CourseRepository(session)
            course_ids = await self._sync_courses(course_repository, schedule, report)
            await self._sync_groups(GroupRepository(session), schedule, course_ids, faculty_row.id, report)
            await self._sync_lecturers(LecturerRepository(session), schedule, faculty_row.id, report)

            if report:
                await session.commit()

        if report:
            logger.info(
                f"Catalog of {faculty.value}: +{report.courses} courses, +{report.groups} groups, "
                f"-{report.deactivated_groups} deactivated, +{report.lecturers} lecturers",
            )
        return report

    @staticmethod
    async def _sync_courses(
        repository: CourseRepository,
        schedule: Schedule,
        report: SyncReport,
    ) -> dict[str, int]:
        """Courses are shared between faculties, so they are matched by name alone."""
        course_ids = await repository.get_ids_by_name()
        missing = sorted(set(schedule.courses) - set(course_ids))
        if not missing:
            return course_ids

        repository.add_many(missing)
        await repository.session.flush()
        report.courses = len(missing)
        return await repository.get_ids_by_name()

    @staticmethod
    async def _sync_groups(
        repository: GroupRepository,
        schedule: Schedule,
        course_ids: dict[str, int],
        faculty_id: int,
        report: SyncReport,
    ) -> None:
        parsed = {
            group_name: course_name
            for course_name, course in schedule.courses.items()
            for group_name in course.groups
        }
        known = {group.name: group for group in await repository.get_by_faculty(faculty_id)}

        for name, course_name in sorted(parsed.items()):
            group = known.get(name)
            if group is None:
                repository.add(Group(name=name, course_id=course_ids[course_name], faculty_id=faculty_id))
                report.groups += 1
                continue
            # a group can move between courses with the academic year, or come back
            group.course_id = course_ids[course_name]
            if not group.is_active:
                group.is_active = True
                report.groups += 1

        for name, group in known.items():
            if name not in parsed and group.is_active:
                group.is_active = False
                report.deactivated_groups += 1

    @staticmethod
    async def _sync_lecturers(
        repository: LecturerRepository,
        schedule: Schedule,
        faculty_id: int,
        report: SyncReport,
    ) -> None:
        known = await repository.get_names_by_faculty(faculty_id)
        missing = sorted({name.strip() for name in schedule.lecturer_names() if name.strip()} - known)
        if not missing:
            return

        repository.add_many(missing, faculty_id)
        report.lecturers = len(missing)
