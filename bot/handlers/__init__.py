from .admin_handler import router as admin_router
from .registration_handler import router as registration_router
from .schedule_handler import router as schedule_router
from .user import router as user_router
from .rating_list_handler import router as rating_list_router

__all__ = [
    "admin_router",
    "registration_router",
    "schedule_router",
    "user_router",
    "rating_list_router",
]
