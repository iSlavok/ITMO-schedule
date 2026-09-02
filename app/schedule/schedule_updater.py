import asyncio
import contextlib
from datetime import UTC, datetime

from loguru import logger

from app.schedule.dated_schedule_builder import DatedScheduleBuilder
from app.schedule.schedule_parser import ScheduleParser
from app.services.schedule_service import ScheduleService


class ScheduleUpdater:
    def __init__(
        self,
        schedule_service: ScheduleService,
        schedule_parser: ScheduleParser,
        dated_schedule_builder: DatedScheduleBuilder,
        interval: int = 600,
    ) -> None:
        self.interval = interval
        self._schedule_service = schedule_service
        self._schedule_parser = schedule_parser
        self._dated_schedule_builder = dated_schedule_builder
        self._task: asyncio.Task | None = None

    async def update_schedule(self) -> None:
        try:
            result = await asyncio.to_thread(self._schedule_parser.parse)
            self._schedule_service.schedule = result.schedule
            logger.success("Schedule updated successfully")
        except Exception as e:
            logger.exception(f"Failed to update schedule: {e}")
            return

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
