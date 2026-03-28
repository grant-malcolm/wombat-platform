# WOMBAT
**Wildlife Observation and Monitoring with Biodiversity Aggregation Technology**

WOMBAT is an open-source citizen science platform for automated wildlife monitoring across Australia. Point a camera at your backyard, bush block, or farm — WOMBAT handles the rest.

---

## What it does

- Ingests images and video from supported wildlife cameras via FTP/SFTP or direct upload
- Detects animals using a pluggable AI detector pipeline (SpeciesNet v4, with more coming)
- Stores detection stills and source video so you can watch animal behaviour, not just see a label
- Routes every AI prediction through a human verification queue before science export
- Exports verified occurrence records in Darwin Core format to the Atlas of Living Australia and the Biodiversity Data Repository

---

## Architecture

```
┌──────────────┐     POST /detect      ┌─────────────────────────┐
│              │ ──────────────────────▶│  detector-placeholder   │  :8100
│   backend    │                        │  (random AU species)    │
│  FastAPI     │ ──────────────────────▶│  detector-speciesnet    │  :8101
│  :8000       │     POST /detect       │  (SpeciesNet v4)        │
│              │                        └─────────────────────────┘
│              │──── PostgreSQL ─────────────────────────────────────────
│              │──── /media (static) ────────────────────────────────────
└──────────────┘
       ▲
       │ /api/*
┌──────────────┐
│   frontend   │
│  React/Vite  │  :5173
└──────────────┘
```

The active detector is selected via the `ACTIVE_DETECTOR` environment variable on the backend. Adding a new AI model means deploying one more microservice behind the same `POST /detect` contract — the backend never changes.

---

## Pluggable detector contract

Every detector microservice implements:

```
GET  /health   → { "status": "ok"|"degraded", "model_loaded": bool, ... }

POST /detect   multipart: file=<image>
               → {
                    "species_common":    "Eastern Quoll",
                    "species_scientific":"Dasyurus viverrinus",
                    "confidence":        0.87,
                    "detector_id":       "speciesnet-v4",
                    "detector_version":  "4.0.1"
                  }
```

---

## Verification workflow

Every new detection arrives as **Pending**. A reviewer can:

| Action | Result |
|--------|--------|
| ✅ Confirm | Marks verified, keeps AI species |
| ✏️ Correct | Marks verified, records human-corrected species |
| 🔄 Re-run | Re-runs inference with a different detector, resets to Pending |
| ❌ Reject | Marks rejected with optional note |

Only **Verified** detections will be exported to ALA / BDR.

---

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/detections/upload` | Upload image or video |
| GET | `/api/detections/?status=all\|pending\|verified\|rejected` | List detections |
| GET | `/api/detections/{id}` | Get single detection |
| POST | `/api/detections/{id}/verify` | Submit review action |
| GET | `/api/detectors/` | List detectors and health |

### Verify request body

```json
{
  "action": "confirm" | "correct" | "reject" | "reprocess",
  "verified_by": "username",
  "verified_species": "Eastern Quoll",
  "verified_species_scientific": "Dasyurus viverrinus",
  "notes": "Reviewer notes",
  "detector_id": "speciesnet"
}
```

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Backend API | Python 3.12 / FastAPI |
| Detector microservices | Python / FastAPI |
| AI model | SpeciesNet v4 (Addax-Data-Science/SPECIESNET-v4-0-1-A-v1) |
| Database | PostgreSQL 16 |
| Media processing | FFmpeg + Pillow |
| Frontend | React 18 / Vite 5 |
| Containers | Docker Compose |

---

## Quick start

```bash
git clone https://github.com/your-org/wombat
cd wombat
cp .env.example .env

docker compose up --build
```

Frontend: http://localhost:5173
Backend API: http://localhost:8001
Placeholder detector: http://localhost:8100
SpeciesNet detector: http://localhost:8101

### Switch to SpeciesNet

Edit `.env`:
```
ACTIVE_DETECTOR=speciesnet
```

Then restart the backend:
```bash
docker compose restart backend
```

> ⚠️ SpeciesNet downloads ~500 MB of model weights on first startup. On CPU, inference takes 30–60 s per image. Check readiness at http://localhost:8101/health.

---

## Roadmap

- [x] Walking skeleton — upload → detect → display
- [x] Video support with linked still/video detections
- [x] Pluggable detector microservice architecture
- [x] SpeciesNet v4 integration
- [x] Human verification queue
- [ ] Multi-camera ingestion (Reolink, smartphone)
- [ ] Occurrence mapping with RASD obfuscation
- [ ] Analytics dashboard
- [ ] Multi-user / camera registration
- [ ] ALA and BDR Darwin Core export
- [ ] iNaturalist cross-posting

---

## Supported cameras

| Camera | Connection | Media |
|--------|-----------|-------|
| Reolink Argus series | FTP/SFTP | JPEG, MP4 |
| Smartphone (Android/iOS) | Direct upload | JPEG |
| Ring | Manual export | MP4 |

More camera types will be added. Contributions welcome.

---

## Contributing

Contributions are welcome. Open an issue or get in touch if you'd like to discuss the project.

## Acknowledgements

WOMBAT builds on [SpeciesNet](https://github.com/google/speciesnet) by Google Research. Location sensitivity guidance follows the [RASD framework](https://www.ala.org.au/rasd) developed by the Atlas of Living Australia and partners.

## Licence

MIT
