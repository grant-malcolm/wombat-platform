"""Placeholder species detector.

Returns randomised data from a curated list of Australian wildlife.
Replace this module with MegaDetector + SpeciesNet integration.
"""

import random

# (common_name, scientific_name)
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


def run_placeholder_detection(frame_path: str) -> dict:
    """Return a random species detection result.

    Args:
        frame_path: Path to the image file (unused by the placeholder).

    Returns:
        Dict with ``species_name`` and ``confidence`` keys.
    """
    common, scientific = random.choice(AUSTRALIAN_SPECIES)
    confidence = round(random.uniform(0.65, 0.99), 2)
    return {
        "species_name": f"{common} ({scientific})",
        "confidence": confidence,
    }
