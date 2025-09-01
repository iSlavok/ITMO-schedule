from pydantic import BaseModel, ConfigDict

from app.enums import UserRole


class CourseDTO(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class GroupDTO(BaseModel):
    id: int
    name: str
    course_id: int
    course: CourseDTO

    model_config = ConfigDict(from_attributes=True)


class UserDTO(BaseModel):
    id: int
    telegram_id: int
    username: str | None
    name: str
    role: UserRole
    group_id: int | None
    group: GroupDTO | None

    model_config = ConfigDict(from_attributes=True)
