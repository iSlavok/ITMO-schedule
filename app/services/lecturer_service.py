from collections.abc import Iterable

from loguru import logger

from app.database import get_session
from app.enums import FacultyCode
from app.repositories import FacultyRepository, LecturerRepository


class LecturerService:
    """Keeps the lecturers table in step with the parsed schedules.

    Ratings are attached to a lecturer row, so a lecturer only becomes rateable
    once such a row exists. Rows are added, never removed: a name that leaves the
    schedule keeps the ratings it has already collected.
    """

    async def sync_from_schedule(self, faculty: FacultyCode, names: Iterable[str]) -> int:
        async with get_session() as session:
            faculty_row = await FacultyRepository(session).get_by_code(faculty)
            if faculty_row is None:
                logger.warning(f"Faculty {faculty.value} is missing, skipping the lecturer sync")
                return 0

            lecturer_repository = LecturerRepository(session)
            known = await lecturer_repository.get_names_by_faculty(faculty_row.id)
            missing = sorted({name.strip() for name in names if name.strip()} - known)
            if not missing:
                return 0

            lecturer_repository.add_many(missing, faculty_row.id)
            await session.commit()

        logger.info(f"Added {len(missing)} new lecturers for {faculty.value}: {', '.join(missing)}")
        return len(missing)
