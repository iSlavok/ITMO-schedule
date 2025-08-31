class ServiceError(Exception):
    pass


class AiServiceError(ServiceError):
    pass


class ClientError(AiServiceError):
    pass


class DateParsingError(AiServiceError):
    pass
