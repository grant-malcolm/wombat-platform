"""SpeciesNet detector microservice.

Wraps the SpeciesNet v4 model (Addax-Data-Science/SPECIESNET-v4-0-1-A-v1) behind
the standard WOMBAT detector REST interface.

The model is downloaded from HuggingFace to /models/speciesnet (a persistent Docker
volume) on first startup. info.json is patched to point the detector field at a local
dummy file so SpeciesNet does not re-download MegaDetector (~150 MB) — we only use
the classifier component.

Geolocation is hardcoded to Western Australia (AUS/WA) and fed to the SpeciesNet
ensemble combiner so that geofencing correctly filters out species outside their
known range (e.g. prefers Southern Brown Bandicoot / Quenda over Northern Brown
Bandicoot for WA detections).

POST /detect accepts a multipart image file and returns a species prediction.
GET /health reports model load status.

CPU inference is supported but may take 30–60 seconds per image.
"""

import json
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
MODEL_DIR = os.environ.get("SPECIESNET_MODEL_DIR", "/models/speciesnet")
DETECTOR_ID = "speciesnet-v4"
DETECTOR_VERSION = "5.0.3"

# Hardcoded geolocation for Western Australia.
GEOLOCATION = {
    "country": "AUS",
    "admin1_region": "Western Australia",
}

_model = None
_ensemble = None
_model_error: str | None = None


def _download_model_if_needed() -> str:
    """Download model from HuggingFace to MODEL_DIR if not already cached.

    Uses info.json as the sentinel — if it exists the download is considered complete.
    Returns the local model directory path.
    """
    from huggingface_hub import snapshot_download  # noqa: PLC0415

    model_dir = Path(MODEL_DIR)
    model_dir.mkdir(parents=True, exist_ok=True)

    if (model_dir / "info.json").exists():
        logger.info("Model already cached at %s", model_dir)
        return str(model_dir)

    logger.info("Downloading SpeciesNet model from HuggingFace: %s → %s", MODEL_ID, model_dir)
    snapshot_download(
        repo_id=MODEL_ID,
        local_dir=str(model_dir),
        local_dir_use_symlinks=False,
    )
    logger.info("Model downloaded successfully.")
    return str(model_dir)


def _patch_info_json(model_dir: str) -> None:
    """Replace any HTTP detector URL in info.json with a local dummy path.

    SpeciesNet reads info.json at load time and downloads MegaDetector if the
    detector field is a URL. Since we only use the classifier, we swap it for a
    local dummy file to skip that download.
    """
    info_path = Path(model_dir) / "info.json"
    if not info_path.exists():
        logger.warning("info.json not found, skipping patch")
        return

    with open(info_path) as f:
        info = json.load(f)

    detector = info.get("detector")
    if isinstance(detector, str) and detector.startswith("http"):
        dummy = Path(model_dir) / "dummy_detector.pt"
        dummy.touch()
        info["detector"] = str(dummy)
        with open(info_path, "w") as f:
            json.dump(info, f, indent=2)
        logger.info("Patched info.json: replaced %s with dummy local path", detector)
    else:
        logger.info("info.json detector field is not a URL, no patch needed")


def _load_model():
    global _model, _ensemble, _model_error
    try:
        model_dir = _download_model_if_needed()
        _patch_info_json(model_dir)

        logger.info("Loading SpeciesNetClassifier and SpeciesNetEnsemble from %s", model_dir)
        from speciesnet import SpeciesNetClassifier, SpeciesNetEnsemble  # noqa: PLC0415

        _model = SpeciesNetClassifier(model_name=model_dir, device="cpu")
        _ensemble = SpeciesNetEnsemble(model_name=model_dir, geofence=True)
        logger.info("SpeciesNet classifier and ensemble loaded successfully.")
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
    """Run SpeciesNet inference with WA geolocation and return the standard detector response."""
    from PIL import Image  # noqa: PLC0415
    from speciesnet import BBox  # noqa: PLC0415

    pil_image = Image.open(image_path).convert("RGB")
    bbox = BBox(xmin=0.0, ymin=0.0, width=1.0, height=1.0)
    preprocessed = _model.preprocess(pil_image, bboxes=[bbox])
    classifier_result = _model.predict(image_path, preprocessed)

    # Build ensemble inputs.
    # We don't run a separate detector — supply a full-frame "animal" detection so
    # the combiner treats the whole image as containing an animal and uses geofencing.
    classifier_results = {image_path: classifier_result}
    detector_results = {
        image_path: {
            "detections": [{"category": "1", "label": "animal", "conf": 1.0, "bbox": [0.0, 0.0, 1.0, 1.0]}]
        }
    }
    geolocation_results = {image_path: GEOLOCATION}

    ensemble_results = _ensemble.combine(
        filepaths=[image_path],
        classifier_results=classifier_results,
        detector_results=detector_results,
        geolocation_results=geolocation_results,
        partial_predictions={},
    )

    result = ensemble_results[0]
    # The ensemble already converts Classification enums to their string values
    label: str = result.get("prediction") or ""
    score: float = float(result.get("prediction_score") or 0.0)

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

    Expected format: "uuid;class;order;family;genus;species;common_name"
    Falls back gracefully for unexpected formats.
    """
    if not label:
        return "Unknown", ""

    parts = [p.strip() for p in label.split(";")]

    if len(parts) >= 7:
        genus = parts[4]
        species_epithet = parts[5]
        common_raw = parts[6]

        # Map special SpeciesNet non-species labels
        if common_raw.lower() == "blank":
            return "empty", ""
        if common_raw.lower() in ("animal", "unknown", "human", "vehicle"):
            return common_raw.title(), ""

        common = common_raw.title() if common_raw else "Unknown"
        if " " in species_epithet:
            scientific = species_epithet.title()
        else:
            scientific = f"{genus} {species_epithet}".strip().title()
        return common, scientific

    # Last resort: use the whole label
    cleaned = label.replace(";", " ").strip().title()
    return cleaned, ""
