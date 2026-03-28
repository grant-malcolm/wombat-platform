# WOMBAT

**Wildlife Observation and Monitoring with Biodiversity Aggregation Technology**

An open-source citizen science platform for automated wildlife monitoring in Australia. Users upload images or videos from camera traps or mobile devices; the platform extracts a representative frame, runs species detection, and stores the results for review and aggregation.

---

## Architecture

```
Browser (React + Vite)
        │
        │ HTTP / multipart upload
        ▼
Backend (FastAPI)  ──►  PostgreSQL  (detections table)
        │
        ├──► Pillow          (normalise uploaded images → JPEG)
        ├──► ffmpeg          (extract frame from video)
        ├──► Detector        (MegaDetector + SpeciesNet — placeholder in v0.1)
        └──► /app/media/     (local filesystem, S3-compatible later)
```

Services are orchestrated with **Docker Compose** for local development.

---

## Quick start

```bash
git clone https://github.com/your-org/wombat.git
cd wombat

# First run — builds images and starts all services
docker compose up --build

# Frontend:  http://localhost:5173
# Backend:   http://localhost:8000
# API docs:  http://localhost:8000/docs
```

The database schema is created automatically on first backend startup.

---

## What has been built (v0.1 — walking skeleton)

This release proves the end-to-end pipeline works before any real AI is integrated.

| # | Capability | Notes |
|---|-----------|-------|
| 1 | **Image upload** | JPEG, PNG, WebP, GIF accepted; normalised to JPEG for storage |
| 2 | **Video upload** | MP4, MOV, AVI, WebM accepted; representative frame extracted at 10 % of duration via ffmpeg |
| 3 | **Placeholder detector** | Returns a random Australian species + confidence score (0.65 – 0.99). Drop-in replacement point for MegaDetector + SpeciesNet |
| 4 | **PostgreSQL persistence** | `detections` table stores filename, media type, frame path, species, confidence, and timestamp |
| 5 | **React UI** | Drag-and-drop upload, live result display, detection history list |

### What is deliberately deferred

- Real AI inference (MegaDetector + SpeciesNet)
- RabbitMQ async processing queue
- S3-compatible media storage
- User accounts and authentication
- Map view and aggregation dashboards
- Alembic database migrations (schema managed via `create_all` for now)

---

## Project layout

```
wombat/
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py          # FastAPI app, lifespan, CORS, static media mount
│       ├── config.py        # Pydantic settings (DATABASE_URL, MEDIA_DIR)
│       ├── database.py      # SQLAlchemy engine + session factory
│       ├── models.py        # Detection ORM model
│       ├── schemas.py       # Pydantic response schemas
│       ├── api/routes/
│       │   └── detections.py   # POST /upload, GET /, GET /{id}
│       └── services/
│           ├── detection.py    # Placeholder detector (swap for real AI here)
│           └── video.py        # ffmpeg frame extraction
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── vite.config.js       # Dev server + proxy to backend
    └── src/
        ├── App.jsx
        ├── index.css
        ├── main.jsx
        └── components/
            ├── UploadForm.jsx
            └── DetectionResult.jsx
```

---

## API reference

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/detections/upload` | Upload image or video; returns detection result |
| `GET`  | `/api/detections/` | List last 50 detections (newest first) |
| `GET`  | `/api/detections/{id}` | Fetch a single detection by UUID |
| `GET`  | `/media/{filename}` | Serve stored JPEG frame |

Interactive docs: `http://localhost:8000/docs`

---

## Development

### Backend only (no Docker)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
DATABASE_URL=postgresql://wombat:wombat@localhost:5432/wombat \
MEDIA_DIR=./media \
uvicorn app.main:app --reload
```

### Frontend only (no Docker)

```bash
cd frontend
npm install
npm run dev
```

Update `vite.config.js` proxy target to `http://localhost:8000` if running the backend outside Docker.

---

## Contributing

Contributions are welcome. Please open an issue before submitting a large pull request so the approach can be discussed first.

## Licence

[Apache 2.0](LICENSE)
