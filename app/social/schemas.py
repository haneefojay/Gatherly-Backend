"""Social schemas (reviews, comments, follows)"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ReviewResponse(BaseModel):
    """Event review response"""

    id: UUID
    rating: int
    title: str | None = None
    content: str
    helpful_count: int
    created_at: datetime
    
    event_id: UUID
    event_title: str | None = None
    
    user_id: UUID
    user_name: str
    user_avatar: str | None = None

    model_config = ConfigDict(from_attributes=True)
