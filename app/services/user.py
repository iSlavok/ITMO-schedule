from app.database import User, Role
from app.repositories import UserRepository


class UserService:
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    def create_user(self, user_id: int, username: str, name: str, role: Role, group_id: int = 0) -> User:
        user = self._user_repo.get_by_user_id(user_id)
        if not user:
            return self._user_repo.create(user_id, username, name, role, group_id)
        return user

    def register_user(self, user: User, group_id: int) -> User:
        user.group_id = group_id
        user.role = Role.USER
        return self._user_repo.update(user)

    def get_user(self, user_id):
        return self._user_repo.get_with_group(user_id)
