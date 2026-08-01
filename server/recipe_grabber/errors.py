class AppError(Exception):
    """An expected application error that is safe to return to the client."""

    def __init__(self, message: str, *, code: str, status: int) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status


class FetchError(AppError):
    def __init__(self, message: str, *, code: str = "fetch_failed", status: int = 422) -> None:
        super().__init__(message, code=code, status=status)


class ValidationError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="invalid_request", status=400)

