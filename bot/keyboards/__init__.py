from .admin_keyboards import get_users_list_kb
from .rating_keyboards import get_add_rating_kb, get_rating_kb, get_to_main_kb
from .rating_list_keyboards import get_main_kb, get_pagination_rating_list_kb, get_rating_list_kb
from .registration_keyboards import get_course_keyboard, get_group_keyboard
from .settings_keyboards import get_user_setting_kb

__all__ = [
    "get_add_rating_kb",
    "get_course_keyboard",
    "get_group_keyboard",
    "get_main_kb",
    "get_pagination_rating_list_kb",
    "get_rating_kb",
    "get_rating_list_kb",
    "get_to_main_kb",
    "get_users_list_kb",
    "get_user_setting_kb",
]
