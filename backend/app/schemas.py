from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel


class DetectionResponse(BaseModel):
    id: UUID
    original_filename: str
    media_type: str
    frame_url: str
    media_url: Optional[str] = None  # URL to original video/image file
    species_name: str
    species_scientific: Optional[str] = None
    confidence: float
    detector_id: Optional[str] = None
    detector_version: Optional[str] = None
    status: str = "pending"
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    verified_species: Optional[str] = None
    verified_species_scientific: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class VerifyRequest(BaseModel):
    action: Literal["confirm", "correct", "reject", "reprocess"]
    verified_by: Optional[str] = None
    verified_species: Optional[str] = None
    verified_species_scientific: Optional[str] = None
    notes: Optional[str] = None
    detector_id: Optional[str] = None  # for reprocess action
