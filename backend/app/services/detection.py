"""Detector client.

Calls the active detector microservice via HTTP and returns a standardised
result dict with keys: species_common, species_scientific, confidence,
detector_id, detector_version.
"""

import httpx

from app.config import settings


def run_detection(frame_path: str, detector_id: str | None = None) -> dict:
    """POST the frame to the active (or specified) detector microservice.

    Args:
        frame_path: Absolute path to the JPEG frame to analyse.
        detector_id: Override the active detector. Defaults to settings.active_detector.

    Returns:
        Dict with keys: species_common, species_scientific, confidence,
        detector_id, detector_version.

    Raises:
        httpx.HTTPError: If the detector service is unreachable or returns an error.
    """
    det_id = detector_id or settings.active_detector
    url = f"{settings.detector_url(det_id)}/detect"

    with open(frame_path, "rb") as fh:
        response = httpx.post(
            url,
            files={"file": ("frame.jpg", fh, "image/jpeg")},
            timeout=120.0,  # SpeciesNet on CPU can take ~60 s
        )
    response.raise_for_status()
    return response.json()
