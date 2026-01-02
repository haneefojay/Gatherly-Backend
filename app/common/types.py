from typing import Literal, NamedTuple


class PaginationParamsType(NamedTuple):
    """
    The pagination parameters for the application.
    """

    q: str | None
    page: int
    size: int
    sort_by: str | None
    order_by: Literal["asc", "desc"]
