"""
Domain-level exceptions raised by the service layer.
API routers translate these into appropriate HTTP responses.
"""


class ServiceError(Exception):
    """Base class for service-layer errors."""


class NotFoundError(ServiceError):
    def __init__(self, entity: str, identifier: str | None = None):
        msg = f"{entity} not found" + (f": {identifier}" if identifier else "")
        super().__init__(msg)


class ConflictError(ServiceError):
    pass


class ValidationError(ServiceError):
    pass


class PermissionDeniedError(ServiceError):
    pass
