from app.database import User
from app.repositories import UserRepository


class AdminService:
    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    def get_users(self) -> list[User]:
        return self._user_repo.get_all()
