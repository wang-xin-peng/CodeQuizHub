from app.core.error_codes import ErrorCode


class AppError(Exception):
    """Base application error."""

    def __init__(self, code: ErrorCode, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class BusinessError(AppError):
    """Business logic error (user-recoverable)."""

    pass


class AuthenticationError(AppError):
    """Authentication error."""

    def __init__(self, message: str = "认证失败", code: ErrorCode = ErrorCode.AUTH_INVALID_CREDENTIALS):
        super().__init__(code, message, 401)


class ForbiddenError(AppError):
    """Permission denied."""

    def __init__(self, message: str = "权限不足"):
        super().__init__(ErrorCode.AUTH_FORBIDDEN, message, 403)


class NotFoundError(AppError):
    """Resource not found."""

    def __init__(self, resource: str, resource_id: str = ""):
        code_name = f"{resource.upper()}_NOT_FOUND"
        try:
            code = ErrorCode(code_name)
        except ValueError:
            code = ErrorCode.INTERNAL_ERROR
        msg = f"{resource} 不存在" if not resource_id else f"{resource}({resource_id}) 不存在"
        super().__init__(code, msg, 404)
