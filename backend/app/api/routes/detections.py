import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Detection
from app.schemas import DetectionResponse, VerifyRequest
from app.services.detection import run_detection
from app.services.video import extract_frame

router = APIRouter()
detectors_router = APIRouter()

IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
VIDEO_CONTENT_TYPES = {"video/mp4", "video/quicktime", "video/x-msvideo", "video/webm"}

KNOWN_DETECTORS = {
    "placeholder": "http://detector-placeholder:8100",
    "speciesnet": "http://detector-speciesnet:8101",
    "megadetector": settings.megadetector_url,
}


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

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
    raw_filename = f"{upload_id}{suffix}"

    if media_type == "video":
        extract_frame(str(raw_path), str(frame_path))
    else:
        from PIL import ImageOps
        with Image.open(raw_path) as img:
            img = ImageOps.exif_transpose(img)
            img.convert("RGB").save(frame_path, "JPEG", quality=85)

    try:
        result = run_detection(str(frame_path))
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Detector error: {exc}",
        ) from exc

    detection = Detection(
        original_filename=file.filename or "upload",
        media_type=media_type,
        stored_frame=frame_filename,
        stored_media=raw_filename,
        species_name=result.get("species_common", "Unknown"),
        species_scientific=result.get("species_scientific"),
        confidence=result.get("confidence", 0.0),
        detector_id=result.get("detector_id"),
        detector_version=result.get("detector_version"),
        status="pending",
    )
    db.add(detection)
    db.commit()
    db.refresh(detection)

    return _to_response(detection)


# ---------------------------------------------------------------------------
# List detections (with optional status filter)
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[DetectionResponse])
def list_detections(status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Detection).order_by(Detection.created_at.desc())
    if status and status != "all":
        query = query.filter(Detection.status == status)
    rows = query.limit(200).all()
    return [_to_response(d) for d in rows]


# ---------------------------------------------------------------------------
# Get single detection
# ---------------------------------------------------------------------------

@router.get("/{detection_id}", response_model=DetectionResponse)
def get_detection(detection_id: str, db: Session = Depends(get_db)):
    detection = db.query(Detection).filter(Detection.id == detection_id).first()
    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found")
    return _to_response(detection)


# ---------------------------------------------------------------------------
# Verify / review a detection
# ---------------------------------------------------------------------------

@router.post("/{detection_id}/verify", response_model=DetectionResponse)
def verify_detection(
    detection_id: str,
    body: VerifyRequest,
    db: Session = Depends(get_db),
):
    detection = db.query(Detection).filter(Detection.id == detection_id).first()
    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found")

    now = datetime.now(timezone.utc)
    reviewer = body.verified_by or "user"

    if body.action == "confirm":
        detection.status = "verified"
        detection.verified_by = reviewer
        detection.verified_at = now
        detection.notes = body.notes

    elif body.action == "correct":
        if not body.verified_species:
            raise HTTPException(
                status_code=422,
                detail="verified_species is required for the 'correct' action.",
            )
        detection.status = "verified"
        detection.verified_by = reviewer
        detection.verified_at = now
        detection.verified_species = body.verified_species
        detection.verified_species_scientific = body.verified_species_scientific
        detection.notes = body.notes

    elif body.action == "reject":
        detection.status = "rejected"
        detection.verified_by = reviewer
        detection.verified_at = now
        detection.notes = body.notes

    elif body.action == "reprocess":
        det_id = body.detector_id or settings.active_detector
        frame_path = str(Path(settings.media_dir) / detection.stored_frame)
        try:
            result = run_detection(frame_path, detector_id=det_id)
        except Exception as exc:
            raise HTTPException(
                status_code=502, detail=f"Detector error: {exc}"
            ) from exc

        detection.species_name = result.get("species_common", detection.species_name)
        detection.species_scientific = result.get("species_scientific", detection.species_scientific)
        detection.confidence = result.get("confidence", detection.confidence)
        detection.detector_id = result.get("detector_id", detection.detector_id)
        detection.detector_version = result.get("detector_version", detection.detector_version)
        detection.status = "pending"
        detection.verified_by = None
        detection.verified_at = None
        detection.verified_species = None
        detection.verified_species_scientific = None
        detection.notes = body.notes

    db.commit()
    db.refresh(detection)
    return _to_response(detection)


# ---------------------------------------------------------------------------
# List available detectors and their health
# ---------------------------------------------------------------------------

@detectors_router.get("/")
def list_detectors():
    results = []
    for det_id, base_url in KNOWN_DETECTORS.items():
        health = _check_detector_health(det_id, base_url)
        results.append(health)
    return results


def _check_detector_health(detector_id: str, base_url: str) -> dict:
    try:
        resp = httpx.get(f"{base_url}/health", timeout=5.0)
        resp.raise_for_status()
        data = resp.json()
        return {
            "detector_id": detector_id,
            "available": True,
            "model_loaded": data.get("model_loaded", False),
            "status": data.get("status", "unknown"),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "detector_id": detector_id,
            "available": False,
            "model_loaded": False,
            "status": "unreachable",
            "error": str(exc),
        }


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _to_response(detection: Detection) -> DetectionResponse:
    media_url = (
        f"/media/{detection.stored_media}"
        if detection.stored_media
        else None
    )
    return DetectionResponse(
        id=detection.id,
        original_filename=detection.original_filename,
        media_type=detection.media_type,
        frame_url=f"/media/{detection.stored_frame}",
        media_url=media_url,
        species_name=detection.species_name,
        species_scientific=detection.species_scientific,
        confidence=detection.confidence,
        detector_id=detection.detector_id,
        detector_version=detection.detector_version,
        status=detection.status or "pending",
        verified_by=detection.verified_by,
        verified_at=detection.verified_at,
        verified_species=detection.verified_species,
        verified_species_scientific=detection.verified_species_scientific,
        notes=detection.notes,
        created_at=detection.created_at,
    )
