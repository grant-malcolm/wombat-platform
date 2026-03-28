import uuid

from sqlalchemy import Column, DateTime, Float, String, Text, func
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base

# Valid status values — stored as plain strings to avoid DDL enum management.
DETECTION_STATUSES = ("pending", "verified", "rejected", "reprocessing")


class Detection(Base):
    __tablename__ = "detections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_filename = Column(String, nullable=False)
    media_type = Column(String, nullable=False)  # "image" | "video"
    stored_frame = Column(String, nullable=False)  # filename of the stored JPEG

    # AI prediction fields
    species_name = Column(String, nullable=False)       # common name
    species_scientific = Column(String, nullable=True)  # scientific name
    confidence = Column(Float, nullable=False)
    detector_id = Column(String, nullable=True)         # e.g. "placeholder"
    detector_version = Column(String, nullable=True)    # e.g. "1.0.0"

    # Verification workflow
    status = Column(String, nullable=False, default="pending")  # see DETECTION_STATUSES
    verified_by = Column(String, nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_species = Column(String, nullable=True)             # human-confirmed common name
    verified_species_scientific = Column(String, nullable=True)  # human-confirmed scientific name
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
