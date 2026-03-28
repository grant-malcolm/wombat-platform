"""MegaDetector + SpeciesNet detector microservice.

Runs MegaDetector v5a as a pre-processing step to locate animals, then
forwards the cropped detection to the SpeciesNet service for species
classification.

POST /detect        — full pipeline: MegaDetector → SpeciesNet
POST /detect-only   — MegaDetector only, returns raw bounding boxes
GET  /health        — model load status
"""

import io
import logging
import os
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image

logger = logging.getLogger("megadetector-detector")
logging.basicConfig(level=logging.INFO)

MODEL_DIR = os.environ.get("MEGADETECTOR_MODEL_DIR", "/models/megadetector")
MODEL_FILENAME = "md_v5a.0.0.pt"
MODEL_URL = (
    "https://github.com/agentmorris/MegaDetector/releases/download/v5.0/md_v5a.0.0.pt"
)

SPECIESNET_URL = os.environ.get("SPECIESNET_URL", "http://detector-speciesnet:8101")

DETECTOR_ID = "megadetector+speciesnet"
DETECTOR_VERSION = "5.0.3"

ANIMAL_CATEGORY = "1"  # MegaDetector: 1=animal, 2=human, 3=vehicle
DETECTION_THRESHOLD = 0.1

_model = None
_model_error: str | None = None


def _download_model_if_needed() -> str:
    """Download md_v5a.0.0.pt to MODEL_DIR if not already present."""
    model_dir = Path(MODEL_DIR)
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / MODEL_FILENAME

    if model_path.exists():
        logger.info("MegaDetector model already cached at %s", model_path)
        return str(model_path)

    logger.info("Downloading MegaDetector model from %s", MODEL_URL)
    try:
        from megadetector.utils.url_utils import download_url  # noqa: PLC0415
        download_url(MODEL_URL, str(model_path))
    except Exception:  # noqa: BLE001
        # Fallback: plain urllib download
        import urllib.request  # noqa: PLC0415
        urllib.request.urlretrieve(MODEL_URL, str(model_path))

    logger.info("MegaDetector model downloaded to %s", model_path)
    return str(model_path)


def _load_model() -> None:
    global _model, _model_error
    try:
        model_path = _download_model_if_needed()
        from megadetector.detection.pytorch_detector import PTDetector  # noqa: PLC0415
        _model = PTDetector(model_path, force_cpu=True)
        logger.info("MegaDetector loaded successfully from %s", model_path)
    except Exception as exc:  # noqa: BLE001
        _model_error = f"{type(exc).__name__}: {exc}"
        logger.error("Failed to load MegaDetector: %s", _model_error)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _load_model()
    yield


app = FastAPI(
    title="WOMBAT MegaDetector + SpeciesNet Detector",
    version=DETECTOR_VERSION,
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    if _model is not None:
        return {
            "status": "ok",
            "model_loaded": True,
            "detector_id": DETECTOR_ID,
        }
    return {
        "status": "degraded",
        "model_loaded": False,
        "detector_id": DETECTOR_ID,
        "error": _model_error,
    }


# ---------------------------------------------------------------------------
# Full pipeline: MegaDetector → SpeciesNet
# ---------------------------------------------------------------------------

@app.post("/detect")
async def detect(file: UploadFile = File(...)):
    if _model is None:
        raise HTTPException(
            status_code=503,
            detail=f"MegaDetector model not loaded: {_model_error}",
        )

    image_bytes = await file.read()
    detections = _run_megadetector(image_bytes)

    animal_detections = [
        d for d in detections
        if d.get("category") == ANIMAL_CATEGORY and d.get("conf", 0) >= DETECTION_THRESHOLD
    ]

    if not animal_detections:
        return {
            "species_common": "empty",
            "species_scientific": "",
            "confidence": 1.0,
            "detector_id": DETECTOR_ID,
            "detector_version": DETECTOR_VERSION,
        }

    best = max(animal_detections, key=lambda d: d["conf"])
    cropped_bytes = _crop_to_bbox(image_bytes, best["bbox"])
    return await _call_speciesnet(cropped_bytes)


# ---------------------------------------------------------------------------
# MegaDetector only (debugging)
# ---------------------------------------------------------------------------

@app.post("/detect-only")
async def detect_only(file: UploadFile = File(...)):
    """Run MegaDetector only and return raw bounding boxes."""
    if _model is None:
        raise HTTPException(
            status_code=503,
            detail=f"MegaDetector model not loaded: {_model_error}",
        )
    image_bytes = await file.read()
    detections = _run_megadetector(image_bytes)
    return {"detections": detections}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_megadetector(image_bytes: bytes) -> list[dict]:
    """Run MegaDetector on raw image bytes; return detections list."""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name

    try:
        img = Image.open(tmp_path).convert("RGB")
        result = _model.generate_detections_one_image(
            img,
            image_id=tmp_path,
            detection_threshold=DETECTION_THRESHOLD,
        )
        return result.get("detections", [])
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def _crop_to_bbox(image_bytes: bytes, bbox: list[float]) -> bytes:
    """Crop image to MegaDetector bbox [xmin, ymin, w, h] (normalised 0–1)."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    w, h = img.size
    xmin, ymin, bw, bh = bbox
    left = max(0, int(xmin * w))
    top = max(0, int(ymin * h))
    right = min(w, int((xmin + bw) * w))
    bottom = min(h, int((ymin + bh) * h))
    crop = img.crop((left, top, right, bottom))
    buf = io.BytesIO()
    crop.save(buf, "JPEG", quality=90)
    return buf.getvalue()


async def _call_speciesnet(image_bytes: bytes) -> dict:
    """POST the cropped image to the SpeciesNet service and return its result
    with the combined detector_id."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{SPECIESNET_URL}/detect",
            files={"file": ("crop.jpg", image_bytes, "image/jpeg")},
        )
        resp.raise_for_status()

    result = resp.json()
    result["detector_id"] = DETECTOR_ID
    result["detector_version"] = DETECTOR_VERSION
    return result
