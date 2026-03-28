from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DetectionResponse(BaseModel):
    id: UUID
    original_filename: str
    media_type: str
    frame_url: str
    species_name: str
    confidence: float
    created_at: datetime

    model_config = {"from_attributes": True}
