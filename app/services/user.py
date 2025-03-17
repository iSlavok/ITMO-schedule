from app.database import User
from app.database.enums import Role
from app.repositories.user import UserRepository


class UserService:
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    def register_user(self, user_id: int, username: str, name: str, role: Role, group_id: int = 0) -> User:
        user = self._user_repo.get_by_user_id(user_id)
        if not user:
            return self._user_repo.create(user_id, username, name, role, group_id)
        return user

    def get_user(self, user_id):
        return self._user_repo.get_with_group(user_id)
