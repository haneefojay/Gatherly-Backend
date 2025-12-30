from typing import Any

from pydantic import BaseModel, Field


class ResponseSchema(BaseModel):
    """This is the generic base response schema"""

    status: str = Field(description="The response status", default="success")
    msg: str = Field(default="Request Successful", description="The response message")
    data: Any = Field(description="The response data")


class PaginationSchema(BaseModel):
    """The generic pagination schema for the application."""

    total_no_items: int = Field(description="The total number of items available")
    total_no_pages: int = Field(description="The total number of pages")
    page: int = Field(description="The current page number")
    size: int = Field(description="Max number of items to return per page")
    count: int = Field(description="The number of items returned")
    has_next_page: bool = Field(description="Indicates if there is a next page")
    has_prev_page: bool = Field(description="Indicates if there is a previous page")


class PaginatedResponseSchema(ResponseSchema):
    """
    Generic schema for paginated responses
    """

    meta: PaginationSchema = Field(description="The pagination metadata")


# Modern generic paginated response
from typing import Generic, List, TypeVar

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response schema"""

    items: List[T]
    total: int
    page: int
    size: int
    pages: int

    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 100,
                "page": 1,
                "size": 10,
                "pages": 10,
            }
        }
