from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.routes import detections
from app.config import settings
from app.database import Base, engine


def _run_migrations():
    """Add new columns to existing tables without dropping data.

    SQLAlchemy create_all() only creates missing tables, not missing columns.
    This function handles the ALTER TABLE statements needed when the schema
    evolves on an already-provisioned database.
    """
    migrations = [
        "ALTER TABLE detections ADD COLUMN IF NOT EXISTS species_scientific VARCHAR",
        "ALTER TABLE detections ADD COLUMN IF NOT EXISTS detector_id VARCHAR",
        "ALTER TABLE detections ADD COLUMN IF NOT EXISTS detector_version VARCHAR",
        "ALTER TABLE detections ADD COLUMN IF NOT EXISTS status VARCHAR NOT NULL DEFAULT 'pending'",
        "ALTER TABLE detections ADD COLUMN IF NOT EXISTS verified_by VARCHAR",
        "ALTER TABLE detections ADD COLUMN IF NOT EXISTS verified_at TIMESTAMPTZ",
        "ALTER TABLE detections ADD COLUMN IF NOT EXISTS verified_species VARCHAR",
        "ALTER TABLE detections ADD COLUMN IF NOT EXISTS verified_species_scientific VARCHAR",
        "ALTER TABLE detections ADD COLUMN IF NOT EXISTS notes TEXT",
    ]
    with engine.begin() as conn:
        for stmt in migrations:
            conn.execute(text(stmt))


@asynccontextmanager
async def lifespan(app: FastAPI):
    media_dir = Path(settings.media_dir)
    media_dir.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    _run_migrations()
    app.mount("/media", StaticFiles(directory=str(media_dir)), name="media")
    yield


app = FastAPI(title="WOMBAT API", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(detections.router, prefix="/api/detections", tags=["detections"])
app.include_router(detections.detectors_router, prefix="/api/detectors", tags=["detectors"])
