import contextlib
import threading
import time
from datetime import UTC, datetime

from app.schedule import ScheduleParser
from app.services.schedule import ScheduleService


class ScheduleUpdater:
    def __init__(self, schedule_service: ScheduleService, schedule_parser: ScheduleParser, interval: int = 600) -> None:
        self.interval = interval
        self._schedule_service = schedule_service
        self._schedule_parser = schedule_parser
        self._thread: threading.Thread | None = None

    def update_schedule(self) -> None:
        data = self._schedule_parser.parse()
        self._schedule_service.schedule = data

    def start_update_loop(self) -> None:
        if self._thread is None or not self._thread.is_alive():
            self._thread = threading.Thread(target=self._update_loop, daemon=True)
            self._thread.start()
        else:
            msg = "ScheduleUpdater is already running"
            raise RuntimeError(msg)

    def _update_loop(self) -> None:
        time.sleep(self.interval)
        while True:
            start_time = datetime.now(tz=UTC)
            with contextlib.suppress(Exception):
                self.update_schedule()
            time.sleep(self.interval-(datetime.now(tz=UTC)-start_time).total_seconds())
