from .user import UserRepository
from .group import GroupRepository
from .course import CourseRepository
from .schedule import ScheduleRepository
from .lecturer import LecturerRepository
from .rating import RatingRepository

__all__ = [
    "UserRepository",
    "GroupRepository",
    "CourseRepository",
    "ScheduleRepository",
    "LecturerRepository",
    "RatingRepository",
]
