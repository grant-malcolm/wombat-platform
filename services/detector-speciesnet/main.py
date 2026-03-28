"""SpeciesNet detector microservice.

Wraps the SpeciesNet v4 model (Addax-Data-Science/SPECIESNET-v4-0-1-A-v1) behind
the standard WOMBAT detector REST interface.

The model is loaded once at startup. POST /detect accepts a multipart image file
and returns a species prediction. GET /health reports model load status.

CPU inference is supported but may take 30–60 seconds per image.
"""

import logging
import os
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile

logger = logging.getLogger("speciesnet-detector")
logging.basicConfig(level=logging.INFO)

MODEL_ID = os.environ.get(
    "SPECIESNET_MODEL", "Addax-Data-Science/SPECIESNET-v4-0-1-A-v1"
)
DETECTOR_ID = "speciesnet-v4"
DETECTOR_VERSION = "4.0.1"

_model = None
_model_error: str | None = None


def _load_model():
    global _model, _model_error
    try:
        logger.info("Importing speciesnet …")
        from speciesnet import SpeciesNet  # noqa: PLC0415

        logger.info("Loading model weights: %s", MODEL_ID)
        _model = SpeciesNet(model_name=MODEL_ID)
        logger.info("SpeciesNet model loaded successfully.")
    except Exception as exc:  # noqa: BLE001
        _model_error = f"{type(exc).__name__}: {exc}"
        logger.error("Failed to load SpeciesNet model: %s", _model_error)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _load_model()
    yield


app = FastAPI(
    title="WOMBAT SpeciesNet Detector",
    version=DETECTOR_VERSION,
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    if _model is not None:
        return {
            "status": "ok",
            "model_loaded": True,
            "detector_id": DETECTOR_ID,
            "model_id": MODEL_ID,
        }
    return {
        "status": "degraded",
        "model_loaded": False,
        "detector_id": DETECTOR_ID,
        "error": _model_error,
    }


@app.post("/detect")
async def detect(file: UploadFile = File(...)):
    if _model is None:
        raise HTTPException(
            status_code=503,
            detail=f"SpeciesNet model not loaded: {_model_error}",
        )

    image_bytes = await file.read()

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name

    try:
        prediction = _run_inference(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return prediction


def _run_inference(image_path: str) -> dict:
    """Run SpeciesNet inference and return the standard detector response."""
    instances = [{"filepath": image_path}]
    results = _model.predict(instances=instances)

    # SpeciesNet returns {"predictions": [{"label": "...", "score": 0.xx, ...}]}
    # The label format is a semicolon-separated taxonomy string:
    #   kingdom;order;family;genus;species_binomial;common_name
    predictions = results.get("predictions", [{}])
    top = predictions[0] if predictions else {}

    label: str = top.get("label", "") or top.get("species", "") or ""
    score: float = float(top.get("score", top.get("confidence", 0.0)))

    common, scientific = _parse_label(label)

    return {
        "species_common": common,
        "species_scientific": scientific,
        "confidence": round(score, 4),
        "detector_id": DETECTOR_ID,
        "detector_version": DETECTOR_VERSION,
    }


def _parse_label(label: str) -> tuple[str, str]:
    """Convert a SpeciesNet taxonomy label to (common_name, scientific_name).

    Expected format: "kingdom;order;family;genus;genus species;common name"
    Falls back gracefully for unexpected formats.
    """
    if not label:
        return "Unknown", "Unknown"

    parts = [p.strip() for p in label.split(";")]

    if len(parts) >= 6:
        scientific = parts[4].title() if parts[4] else parts[3].title()
        common = parts[5].title() if parts[5] else scientific
        return common, scientific

    if len(parts) >= 5:
        scientific = parts[4].title()
        return scientific, scientific

    # Last resort: use the whole label
    cleaned = label.replace(";", " ").strip().title()
    return cleaned, cleaned
