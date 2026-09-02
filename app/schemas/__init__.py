from .ai_schemas import AiDate, AiDateResponse, AiNoteOperation, AiNoteResponse
from .rating_schemas import LecturerDTO
from .schedule_schemas import (
    DatedLesson,
    DatedSchedule,
    Lesson,
    LessonPatch,
    ParseResult,
    Schedule,
    ScheduleCourse,
    ScheduleDay,
    ScheduleGroup,
    ScheduleNote,
    ScheduleWeek,
)
from .users_schemas import CourseDTO, GroupDTO, UserDTO, UserSettings, UserWithGroupDTO

__all__ = [
    "AiDate",
    "AiDateResponse",
    "AiNoteOperation",
    "AiNoteResponse",
    "CourseDTO",
    "DatedLesson",
    "DatedSchedule",
    "GroupDTO",
    "LecturerDTO",
    "Lesson",
    "LessonPatch",
    "ParseResult",
    "Schedule",
    "ScheduleCourse",
    "ScheduleDay",
    "ScheduleGroup",
    "ScheduleNote",
    "ScheduleWeek",
    "UserDTO",
    "UserSettings",
    "UserWithGroupDTO",
]
