from pathlib import Path

import yaml
from pydantic import BaseModel


class RegistrationMessages(BaseModel):
    course_request: str
    course_selected: str
    group_request: str
    group_selected: str


class UsersListMessage(BaseModel):
    header: str
    user: str


class AdminMessages(BaseModel):
    users_list: UsersListMessage


class LessonScheduleMessage(BaseModel):
    number: str
    name: str
    type: str
    lecturer: str
    lecturer_rating: str
    room: str
    end: str


class ScheduleMessages(BaseModel):
    not_loaded_error: str
    header: str
    lesson: LessonScheduleMessage


class LecturerRatingListMessages(BaseModel):
    type_request: str
    best_header: str
    worst_header: str
    lecturer: str


class RatingAlerts(BaseModel):
    lecturer_not_found: str
    lecturer_already_rated: str
    lecturer_no_lecture_today: str


class RatingMessages(BaseModel):
    no_available_lecturers: str
    lecturer_request: str
    rating_request: str
    rating_added: str
    alerts: RatingAlerts


class NotificationMessages(BaseModel):
    lecturer_rating: str


class Buttons(BaseModel):
    today_schedule: str
    tomorrow_schedule: str
    lecturer_rating: str
    lecturer_rating_list: str
    best_lecturers: str
    worst_lecturers: str
    back: str
    pagination_next: str
    pagination_prev: str


class Messages(BaseModel):
    registration: RegistrationMessages
    admin: AdminMessages
    schedule: ScheduleMessages
    lecturer_rating_list: LecturerRatingListMessages
    rating: RatingMessages
    notification: NotificationMessages
    buttons: Buttons


def load_messages() -> Messages:
    path = Path("messages.yaml")
    with path.open(encoding="utf-8") as file:
        data = yaml.safe_load(file)
        return Messages(**data)


messages = load_messages()
