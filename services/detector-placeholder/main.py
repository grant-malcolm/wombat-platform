"""Placeholder detector microservice.

Returns a random Australian wildlife species with a random confidence score.
Implements the standard WOMBAT detector REST interface.
"""

import random

from fastapi import FastAPI, File, UploadFile

AUSTRALIAN_SPECIES = [
    ("Eastern Grey Kangaroo", "Macropus giganteus"),
    ("Red Kangaroo", "Osphranter rufus"),
    ("Common Wombat", "Vombatus ursinus"),
    ("Laughing Kookaburra", "Dacelo novaeguineae"),
    ("Short-beaked Echidna", "Tachyglossus aculeatus"),
    ("Common Brushtail Possum", "Trichosurus vulpecula"),
    ("Common Ringtail Possum", "Pseudocheirus peregrinus"),
    ("Sugar Glider", "Petaurus breviceps"),
    ("Quokka", "Setonix brachyurus"),
    ("Koala", "Phascolarctos cinereus"),
    ("Platypus", "Ornithorhynchus anatinus"),
    ("Wedge-tailed Eagle", "Aquila audax"),
    ("Sulphur-crested Cockatoo", "Cacatua galerita"),
    ("Emu", "Dromaius novaehollandiae"),
    ("Eastern Blue-tongue Lizard", "Tiliqua scincoides"),
    ("Lace Monitor", "Varanus varius"),
    ("Spotted-tailed Quoll", "Dasyurus maculatus"),
    ("Numbat", "Myrmecobius fasciatus"),
    ("Bilby", "Macrotis lagotis"),
]

DETECTOR_ID = "placeholder"
DETECTOR_VERSION = "1.0.0"

app = FastAPI(title="WOMBAT Placeholder Detector", version=DETECTOR_VERSION)


@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": True, "detector_id": DETECTOR_ID}


@app.post("/detect")
async def detect(file: UploadFile = File(...)):
    # Image bytes are accepted but not used — this is a placeholder.
    await file.read()

    common, scientific = random.choice(AUSTRALIAN_SPECIES)
    confidence = round(random.uniform(0.65, 0.99), 2)

    return {
        "species_common": common,
        "species_scientific": scientific,
        "confidence": confidence,
        "detector_id": DETECTOR_ID,
        "detector_version": DETECTOR_VERSION,
    }
