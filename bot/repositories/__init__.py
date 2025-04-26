from .user import UserRepository
from .group import GroupRepository
from .course import CourseRepository
from .schedule import ScheduleRepository
from .lecturer import LecturerRepository
from .rating import RatingRepository
from .log import LogRepository

__all__ = [
    "UserRepository",
    "GroupRepository",
    "CourseRepository",
    "ScheduleRepository",
    "LecturerRepository",
    "RatingRepository",
    "LogRepository",
]
