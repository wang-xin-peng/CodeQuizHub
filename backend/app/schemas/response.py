from typing import Any

from pydantic import BaseModel


class SuccessResponse(BaseModel):
    code: int = 0
    data: Any = None
    message: str = "success"


class PaginatedData(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int


class PaginatedResponse(BaseModel):
    code: int = 0
    data: PaginatedData
    message: str = "success"


class ErrorResponse(BaseModel):
    code: str
    message: str
    detail: Any = None


def success_response(data: Any = None, message: str = "success") -> dict:
    return {"code": 0, "data": data, "message": message}


def paginated_response(items: list, total: int, page: int, page_size: int) -> dict:
    return {
        "code": 0,
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        },
        "message": "success",
    }
