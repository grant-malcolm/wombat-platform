"""Analytics / stats endpoints for the WOMBAT dashboard.

GET /api/stats/overview               — quick stats row
GET /api/stats/species-over-time      — time-series by species (verified only)
GET /api/stats/species-composition    — donut breakdown (verified only)
GET /api/stats/activity-by-hour       — 24-hour histogram (all detections)
"""

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Detection

router = APIRouter()

# Species to exclude from "interesting" counts
_NON_SPECIES = {"empty", "unknown", "blank", "animal", "human", "vehicle"}


def _effective_species(d: Detection) -> str:
    """Return the authoritative species name for a detection."""
    return (d.verified_species or d.species_name or "").strip()


# ---------------------------------------------------------------------------
# Overview — quick stats row
# ---------------------------------------------------------------------------

@router.get("/overview")
def get_overview(db: Session = Depends(get_db)):
    all_detections = db.query(Detection).all()
    total = len(all_detections)
    verified = sum(1 for d in all_detections if d.status == "verified")
    pending = sum(1 for d in all_detections if d.status == "pending")

    species_set = {
        _effective_species(d).lower()
        for d in all_detections
        if d.status == "verified" and _effective_species(d).lower() not in _NON_SPECIES
    }

    return {
        "total_detections": total,
        "verified_count": verified,
        "pending_count": pending,
        "species_count": len(species_set),
    }


# ---------------------------------------------------------------------------
# Species over time — line/bar chart
# ---------------------------------------------------------------------------

@router.get("/species-over-time")
def get_species_over_time(days: int = 7, db: Session = Depends(get_db)):
    """Return daily detection counts per species for verified detections.

    ?days=7   → last 7 days
    ?days=30  → last 30 days
    ?days=0   → all time
    """
    now = datetime.now(timezone.utc)
    query = db.query(Detection).filter(Detection.status == "verified")
    if days > 0:
        query = query.filter(Detection.created_at >= now - timedelta(days=days))
    detections = query.all()

    # Aggregate: date → species → count
    date_species: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    species_totals: dict[str, int] = defaultdict(int)

    for d in detections:
        date_str = d.created_at.strftime("%Y-%m-%d")
        species = _effective_species(d)
        if not species or species.lower() in _NON_SPECIES:
            continue
        date_species[date_str][species] += 1
        species_totals[species] += 1

    # Top 5 species by total count; everything else → "Other"
    top5 = sorted(species_totals, key=lambda s: species_totals[s], reverse=True)[:5]
    top5_set = set(top5)

    # Build sorted date list (fill gaps if days > 0)
    if days > 0 and date_species:
        start = now - timedelta(days=days)
        date_list = [
            (start + timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(days + 1)
        ]
    else:
        date_list = sorted(date_species)

    data = []
    has_other = False
    for date_str in date_list:
        entry: dict = {"date": date_str}
        other = 0
        for species, count in date_species.get(date_str, {}).items():
            if species in top5_set:
                entry[species] = entry.get(species, 0) + count
            else:
                other += count
        if other:
            entry["Other"] = other
            has_other = True
        data.append(entry)

    species_keys = top5 + (["Other"] if has_other else [])

    return {"data": data, "species": species_keys}


# ---------------------------------------------------------------------------
# Species composition — donut chart
# ---------------------------------------------------------------------------

@router.get("/species-composition")
def get_species_composition(db: Session = Depends(get_db)):
    """Return species breakdown as % of total verified detections (top 8 + Other)."""
    detections = db.query(Detection).filter(Detection.status == "verified").all()

    counts: dict[str, int] = defaultdict(int)
    for d in detections:
        species = _effective_species(d)
        if not species or species.lower() in _NON_SPECIES:
            continue
        counts[species] += 1

    total = sum(counts.values())
    if total == 0:
        return []

    top8 = sorted(counts, key=lambda s: counts[s], reverse=True)[:8]
    other_count = sum(v for k, v in counts.items() if k not in top8)

    result = [
        {
            "species": s,
            "count": counts[s],
            "pct": round(counts[s] / total * 100, 1),
        }
        for s in top8
    ]
    if other_count:
        result.append({
            "species": "Other",
            "count": other_count,
            "pct": round(other_count / total * 100, 1),
        })
    return result


# ---------------------------------------------------------------------------
# Activity by hour — 24-hour histogram
# ---------------------------------------------------------------------------

@router.get("/activity-by-hour")
def get_activity_by_hour(db: Session = Depends(get_db)):
    """Return detection counts grouped by hour of day (0–23), all detections."""
    detections = db.query(Detection).all()

    counts = [0] * 24
    for d in detections:
        if d.created_at:
            counts[d.created_at.hour] += 1

    return [{"hour": h, "count": counts[h]} for h in range(24)]
