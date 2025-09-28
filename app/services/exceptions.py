class ServiceError(Exception):
    """Base class for all service-related errors."""


class RatingServiceError(ServiceError):
    """Base class for all rating service errors."""


class ScheduleServiceError(ServiceError):
    """Base class for all schedule service errors."""


class UserCannotRateLecturerError(RatingServiceError):
    """Raised when a user tries to rate a lecturer they are not allowed to."""
    def __init__(self, message: str = "User cannot rate this lecturer") -> None:
        super().__init__(message)


class ScheduleNotLoadedError(ScheduleServiceError):
    """Raised when trying to access the schedule before it has been loaded."""
    def __init__(self, message: str = "Schedule has not been loaded yet") -> None:
        super().__init__(message)
