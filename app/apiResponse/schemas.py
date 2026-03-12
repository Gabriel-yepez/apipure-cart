from typing import Any, Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    """Standardized API response structure."""
    ok: bool
    data: Optional[T] = None
    messages: str = ""

def create_response(
    data: Any = None, 
    ok: bool = True, 
    messages: str = ""
) -> ApiResponse:
    """Helper function to build a standardized API response."""
    return ApiResponse(ok=ok, data=data, messages=messages)
