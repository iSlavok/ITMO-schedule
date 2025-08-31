from .admin_keyboards import get_users_list_kb
from .registration_keyboards import get_course_keyboard, get_group_keyboard
from .user import get_add_rating_kb, get_main_kb, get_pagination_rating_kb, get_rating_kb

__all__ = [
    "get_add_rating_kb",
    "get_course_keyboard",
    "get_group_keyboard",
    "get_main_kb",
    "get_pagination_rating_kb",
    "get_rating_kb",
    "get_users_list_kb",
]
