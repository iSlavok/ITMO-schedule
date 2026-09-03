from pydantic import BaseModel, ConfigDict

from app.enums import FacultyCode, UserRole


class CourseDTO(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class FacultyDTO(BaseModel):
    id: int
    code: FacultyCode
    name: str

    model_config = ConfigDict(from_attributes=True)


class GroupDTO(BaseModel):
    id: int
    name: str
    course_id: int
    faculty_id: int
    course: CourseDTO
    faculty: FacultyDTO

    model_config = ConfigDict(from_attributes=True)


class UserWithGroupDTO(BaseModel):
    id: int
    telegram_id: int
    username: str | None
    name: str
    role: UserRole
    group_id: int | None
    group: GroupDTO | None

    model_config = ConfigDict(from_attributes=True)


class UserDTO(BaseModel):
    id: int
    telegram_id: int
    username: str | None
    name: str
    role: UserRole
    group_id: int

    model_config = ConfigDict(from_attributes=True)


class UserSettings(BaseModel):
    rating_notifications: bool
