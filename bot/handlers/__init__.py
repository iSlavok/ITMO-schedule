from .admin_handler import router as admin_router
from .rating_handler import router as rating_router
from .rating_list_handler import router as rating_list_router
from .registration_handler import router as registration_router
from .schedule_handler import router as schedule_router
from .rating_notification_handler import schedule_jobs
from .settings_handler import router as settings_router

__all__ = [
    "admin_router",
    "rating_list_router",
    "rating_router",
    "registration_router",
    "schedule_router",
    "settings_router",
    "schedule_jobs",
]
