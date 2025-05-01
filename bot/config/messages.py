from pydantic import BaseModel
import yaml


class UsersListMessage(BaseModel):
    header: str
    user: str


class AdminMessages(BaseModel):
    users_list: UsersListMessage


class RegistrationMessages(BaseModel):
    course_request: str
    course_selected: str
    group_request: str
    group_selected: str


class Messages(BaseModel):
    registration: RegistrationMessages
    admin: AdminMessages


def load() -> Messages:
    with open("messages.yaml", "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
        return Messages(**data)


messages = load()
