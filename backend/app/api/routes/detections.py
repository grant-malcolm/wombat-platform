import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Detection
from app.schemas import DetectionResponse
from app.services.detection import run_placeholder_detection
from app.services.video import extract_frame

router = APIRouter()

IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
VIDEO_CONTENT_TYPES = {"video/mp4", "video/quicktime", "video/x-msvideo", "video/webm"}


@router.post("/upload", response_model=DetectionResponse, status_code=201)
def upload_media(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content_type = (file.content_type or "").split(";")[0].strip()

    if content_type in IMAGE_CONTENT_TYPES:
        media_type = "image"
    elif content_type in VIDEO_CONTENT_TYPES:
        media_type = "video"
    else:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported media type '{content_type}'. "
                   "Accepted: JPEG, PNG, WebP, GIF, MP4, MOV, AVI, WebM.",
        )

    media_dir = Path(settings.media_dir)
    upload_id = uuid.uuid4().hex
    suffix = Path(file.filename or "upload").suffix or ".bin"
    raw_path = media_dir / f"{upload_id}{suffix}"

    with raw_path.open("wb") as fh:
        shutil.copyfileobj(file.file, fh)

    frame_filename = f"{upload_id}.jpg"
    frame_path = media_dir / frame_filename

    if media_type == "video":
        extract_frame(str(raw_path), str(frame_path))
    else:
        with Image.open(raw_path) as img:
            img.convert("RGB").save(frame_path, "JPEG", quality=85)

    result = run_placeholder_detection(str(frame_path))

    detection = Detection(
        original_filename=file.filename or "upload",
        media_type=media_type,
        stored_frame=frame_filename,
        species_name=result["species_name"],
        confidence=result["confidence"],
    )
    db.add(detection)
    db.commit()
    db.refresh(detection)

    return _to_response(detection)


@router.get("/", response_model=list[DetectionResponse])
def list_detections(db: Session = Depends(get_db)):
    rows = (
        db.query(Detection)
        .order_by(Detection.created_at.desc())
        .limit(50)
        .all()
    )
    return [_to_response(d) for d in rows]


@router.get("/{detection_id}", response_model=DetectionResponse)
def get_detection(detection_id: str, db: Session = Depends(get_db)):
    detection = db.query(Detection).filter(Detection.id == detection_id).first()
    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found")
    return _to_response(detection)


def _to_response(detection: Detection) -> DetectionResponse:
    return DetectionResponse(
        id=detection.id,
        original_filename=detection.original_filename,
        media_type=detection.media_type,
        frame_url=f"/media/{detection.stored_frame}",
        species_name=detection.species_name,
        confidence=detection.confidence,
        created_at=detection.created_at,
    )
