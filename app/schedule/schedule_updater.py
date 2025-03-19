import datetime
import time
import threading

from typing import TYPE_CHECKING

from .schedule_parser import ScheduleParser

if TYPE_CHECKING:
    from app.services import ScheduleService


class ScheduleUpdater:
    def __init__(self, schedule_service: "ScheduleService", schedule_parser: ScheduleParser, interval: int = 600):
        self.interval = interval
        self._schedule_service = schedule_service
        self._schedule_parser = schedule_parser
        self._thread = threading.Thread(target=self._update_loop, daemon=True)
        self._thread.start()

    def _update_loop(self):
        while True:
            start_time = datetime.datetime.now()
            # try:
            self._update_schedule()
            print(f"[{datetime.datetime.now()}] Расписание обновлено.")
            # except Exception as e:
            #     print(f"[{datetime.datetime.now()}] Ошибка при обновлении расписания: {str(e)}")
            time.sleep(self.interval-(datetime.datetime.now()-start_time).total_seconds())

    def _update_schedule(self):
        data = self._schedule_parser.parse()
        self._schedule_service.schedule = data
