import asyncio
import contextlib
from datetime import UTC, datetime
from typing import Protocol

from loguru import logger

from app.enums import FacultyCode
from app.schedule.dated_schedule_builder import DatedScheduleBuilder
from app.schemas import ParseResult
from app.services.catalog_service import CatalogService
from app.services.schedule_service import ScheduleService


class ScheduleSource(Protocol):
    """A parser of one faculty's schedule sheet. Blocking: it goes to the network."""

    def parse(self) -> ParseResult: ...


class ScheduleUpdater:
    """Refreshes one faculty's schedule on a loop.

    Each faculty gets its own updater, so a sheet that fails to parse only leaves
    that faculty on its previous data. A successful parse also feeds the catalog
    of courses, groups and lecturers. The dated overlay is built from sheet
    footnotes and only exists for faculties whose sheet carries them.
    """

    def __init__(
        self,
        schedule_service: ScheduleService,
        schedule_parser: ScheduleSource,
        faculty: FacultyCode,
        *,
        catalog_service: CatalogService | None = None,
        dated_schedule_builder: DatedScheduleBuilder | None = None,
        interval: int = 600,
    ) -> None:
        self.interval = interval
        self._schedule_service = schedule_service
        self._schedule_parser = schedule_parser
        self._faculty = faculty
        self._catalog_service = catalog_service
        self._dated_schedule_builder = dated_schedule_builder
        self._task: asyncio.Task | None = None

    async def update_schedule(self) -> None:
        try:
            result = await asyncio.to_thread(self._schedule_parser.parse)
            self._schedule_service.set_faculty_schedule(self._faculty, result.schedule)
            logger.success(f"Schedule of {self._faculty.value} updated successfully")
        except Exception as e:
            logger.exception(f"Failed to update the schedule of {self._faculty.value}: {e}")
            return

        if self._catalog_service is not None:
            try:
                await self._catalog_service.sync_from_schedule(self._faculty, result.schedule)
            except Exception as e:
                logger.exception(f"Failed to sync the catalog of {self._faculty.value}: {e}")

        if self._dated_schedule_builder is not None:
            try:
                self._schedule_service.dated_schedule = await self._dated_schedule_builder.build(result)
                logger.success("Dated schedule rebuilt successfully")
            except Exception as e:
                logger.exception(f"Failed to rebuild dated schedule: {e}")

    def start_update_loop(self) -> None:
        if self._task is not None and not self._task.done():
            msg = "ScheduleUpdater is already running"
            raise RuntimeError(msg)
        self._task = asyncio.create_task(self._update_loop())

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._task
        self._task = None

    async def _update_loop(self) -> None:
        while True:
            await asyncio.sleep(self.interval)
            start_time = datetime.now(tz=UTC)
            await self.update_schedule()
            elapsed = (datetime.now(tz=UTC) - start_time).total_seconds()
            await asyncio.sleep(max(0.0, self.interval - elapsed))
