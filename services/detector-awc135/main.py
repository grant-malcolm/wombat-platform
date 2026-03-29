"""AWC135 detector microservice.

Uses MegaDetector to locate animals, then classifies each crop with the
Australian Wildlife Conservancy's AWC-135 EfficientNetV2S classifier
(135 Australian species, ~1.1 M verified camera-trap training images).

POST /detect    — full pipeline: MegaDetector bbox → AWC135 crop classify
GET  /health    — model load status
"""

import io
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import torch
import torchvision.transforms as T
from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image

logger = logging.getLogger("awc135-detector")
logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

MODEL_DIR = os.environ.get("AWC135_MODEL_DIR", "/models/awc135")
MODEL_FILENAME = "awc-135-v1.pth"
LABELS_FILENAME = "labels.txt"
MODEL_URL = (
    "https://github.com/Australian-Wildlife-Conservancy-AWC/awc-wildlife-classifier"
    "/releases/download/awc-135/awc-135-v1.pth"
)
LABELS_URL = (
    "https://raw.githubusercontent.com/Australian-Wildlife-Conservancy-AWC"
    "/awc-wildlife-classifier/main/labels.txt"
)

MEGADETECTOR_URL = os.environ.get("MEGADETECTOR_URL", "http://detector-megadetector:8102")

DETECTOR_ID = "awc135"
DETECTOR_VERSION = "1.0"

ANIMAL_CATEGORY = "1"  # MegaDetector: 1=animal, 2=human, 3=vehicle
DETECTION_THRESHOLD = 0.1

INPUT_SIZE = 384
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------

_model = None
_labels: list[str] = []
_model_error: str | None = None

_transform = T.Compose([
    T.Resize((INPUT_SIZE, INPUT_SIZE)),
    T.ToTensor(),
    T.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
])


# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------

def _download_file_if_needed(url: str, dest: Path) -> None:
    if dest.exists():
        logger.info("File already cached at %s", dest)
        return
    logger.info("Downloading %s -> %s", url, dest)
    import urllib.request
    urllib.request.urlretrieve(url, str(dest))
    logger.info("Download complete: %s", dest)


def _load_model() -> None:
    global _model, _labels, _model_error
    try:
        model_dir = Path(MODEL_DIR)
        model_dir.mkdir(parents=True, exist_ok=True)

        model_path = model_dir / MODEL_FILENAME
        labels_path = model_dir / LABELS_FILENAME

        _download_file_if_needed(MODEL_URL, model_path)
        _download_file_if_needed(LABELS_URL, labels_path)

        _labels = labels_path.read_text().splitlines()
        logger.info("Loaded %d labels", len(_labels))

        import timm  # noqa: PLC0415
        model = timm.create_model(
            "tf_efficientnetv2_s",
            pretrained=False,
            num_classes=len(_labels),
        )
        model.load_state_dict(
            torch.load(str(model_path), map_location="cpu", weights_only=True)
        )
        model.eval()
        _model = model
        logger.info("AWC135 model loaded successfully from %s", model_path)

    except Exception as exc:  # noqa: BLE001
        _model_error = f"{type(exc).__name__}: {exc}"
        logger.error("Failed to load AWC135 model: %s", _model_error)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _load_model()
    yield


app = FastAPI(
    title="WOMBAT AWC135 Detector",
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
            "version": DETECTOR_VERSION,
        }
    return {
        "status": "degraded",
        "model_loaded": False,
        "detector_id": DETECTOR_ID,
        "version": DETECTOR_VERSION,
        "error": _model_error,
    }


# ---------------------------------------------------------------------------
# Detect
# ---------------------------------------------------------------------------

@app.post("/detect")
async def detect(file: UploadFile = File(...)):
    if _model is None:
        raise HTTPException(
            status_code=503,
            detail=f"AWC135 model not loaded: {_model_error}",
        )

    image_bytes = await file.read()

    # Step 1: call MegaDetector for bounding boxes
    detections, img_width, img_height = await _call_megadetector(image_bytes, file.filename)

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

    # Step 2: crop the highest-confidence animal detection
    best = max(animal_detections, key=lambda d: d["conf"])
    crop = _crop_to_bbox(image_bytes, best["bbox"])

    # Step 3: classify with AWC135
    species_common, confidence = _classify(crop)

    return {
        "species_common": species_common,
        "species_scientific": "",
        "confidence": confidence,
        "detector_id": DETECTOR_ID,
        "detector_version": DETECTOR_VERSION,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _call_megadetector(
    image_bytes: bytes, filename: str | None
) -> tuple[list[dict], int, int]:
    """POST image to MegaDetector /detect-only; return (detections, w, h)."""
    fname = filename or "image.jpg"
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{MEGADETECTOR_URL}/detect-only",
            files={"file": (fname, image_bytes, "image/jpeg")},
        )
        resp.raise_for_status()

    data = resp.json()
    img = Image.open(io.BytesIO(image_bytes))
    w, h = img.size
    # Prefer dimensions from response if present
    img_width = data.get("image_width", w)
    img_height = data.get("image_height", h)
    return data.get("detections", []), img_width, img_height


def _crop_to_bbox(image_bytes: bytes, bbox: list[float]) -> Image.Image:
    """Crop image to MegaDetector bbox [xmin, ymin, w, h] (normalised 0–1)."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    w, h = img.size
    xmin, ymin, bw, bh = bbox
    left = max(0, int(xmin * w))
    top = max(0, int(ymin * h))
    right = min(w, int((xmin + bw) * w))
    bottom = min(h, int((ymin + bh) * h))
    return img.crop((left, top, right, bottom))


def _classify(crop: Image.Image) -> tuple[str, float]:
    """Run AWC135 classifier on a PIL crop; return (label, confidence)."""
    tensor = _transform(crop).unsqueeze(0)  # (1, 3, 384, 384)
    with torch.no_grad():
        logits = _model(tensor)
        probs = torch.softmax(logits, dim=1)[0]
    idx = int(probs.argmax())
    confidence = float(probs[idx])
    label = _labels[idx] if idx < len(_labels) else f"class_{idx}"
    return label, confidence
