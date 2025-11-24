from fastapi import HTTPException, status


class DareZoneException(Exception):
    """Base exception for DareZone"""

    pass


class AuthenticationError(DareZoneException):
    """Authentication failed"""

    pass


class AuthorizationError(DareZoneException):
    """User not authorized"""

    pass


class ValidationError(DareZoneException):
    """Input validation failed"""

    pass


class NotFoundError(DareZoneException):
    """Resource not found"""

    pass


# HTTP Exception helpers
def unauthorized_exception(detail: str = "Not authenticated"):
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def forbidden_exception(detail: str = "Not authorized"):
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def not_found_exception(detail: str = "Resource not found"):
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
