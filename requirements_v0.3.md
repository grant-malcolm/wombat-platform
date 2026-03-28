# WOMBAT Platform Requirements v0.3

## Vision
A citizen science wildlife monitoring platform for Australia. Participants deploy cameras, the platform handles AI species detection, and the aggregated data contributes to national biodiversity science. Public engagement through video and beautiful visualisation; hard science through standards-compliant data export.

---

## Architecture principles

### Pluggable detector registry
- Each detector implements a standard interface: image in → species prediction out
- Detectors run as independent microservices behind a common API contract
- Account owners can select preferred detector per project
- Multiple detectors can be run on same media for comparison
- New detectors can be added without changing core platform

**Current detectors:**
- Placeholder (random Australian species — testing only) — port 8100
- SpeciesNet v5.0.3 (Google) — port 8101
- MegaDetector + SpeciesNet (MegaDetector crops → SpeciesNet classifies) — port 8102

**Future detectors:**
- DeepFaune (CNRS)
- iNaturalist Computer Vision API

### Human-in-the-loop verification
AI provides first cut, humans verify before science export. Inspired by MATE's QA workflow.
Only verified records exported to ALA/BDR/iNaturalist.

---

## Geolocation strategy

### Priority order for detection geolocation
1. **EXIF GPS** — extract lat/long from image metadata at ingestion
2. **Camera location** — if no EXIF GPS, use the registered location for that camera
3. **Account default** — if no camera location, use account-level default location
4. **None** — record without geolocation, flag for review

### Geolocation passed to SpeciesNet ensemble
- Enables geofencing — species predictions weighted by known range
- Fixes species disambiguation (e.g. quenda vs northern brown bandicoot)
- Required for RASD compliance and Darwin Core export

### Camera location (important for video)
- Videos rarely carry GPS metadata
- When a camera is registered, user sets a location (lat/long or place name)
- Location stored with camera record
- All detections from that camera inherit camera location unless EXIF overrides
- Benefits: video geolocation, EXIF-less image geolocation, RASD compliance, Darwin Core export

### Location storage
- Full precision coordinates always stored internally
- Display precision governed by RASD species sensitivity framework:
  - Sensitive species → 10km grid
  - Near-sensitive → 1km grid  
  - General → exact or minimal obfuscation
- Participant can always see their own exact data
- Public aggregated view always obfuscated

---

## Data model

### Detection record
| Field | Description |
|-------|-------------|
| id | UUID |
| media_id | Link to source image or video |
| frame_path | Path to extracted frame (if video) |
| detector_id | Which detector made this prediction |
| detector_version | Version of the detector |
| detected_species | Common name from detector |
| detected_species_scientific | Scientific name from detector |
| confidence | Confidence score 0-1 |
| status | pending / verified / rejected / reprocessing |
| verified_by | User who verified (nullable) |
| verified_at | Timestamp of verification (nullable) |
| verified_species | Human-confirmed species (may differ from detected) |
| verified_species_scientific | Human-confirmed scientific name |
| notes | Reviewer notes |
| created_at | Detection timestamp |

### Media record
| Field | Description |
|-------|-------------|
| id | UUID |
| camera_id | Source camera (nullable until camera registration built) |
| media_type | image / video |
| original_filename | As uploaded |
| stored_path | Internal storage path |
| captured_at | Timestamp from EXIF or filename |
| latitude | Full precision — from EXIF, then camera location, then null |
| longitude | Full precision |
| latitude_source | exif / camera / account / none |
| datum | Coordinate datum (WGS84) |
| licence | CC0 / CC-BY per participant setting |

### Camera record (future sprint)
| Field | Description |
|-------|-------------|
| id | UUID |
| user_id | Owner |
| name | User-defined label |
| camera_type | reolink / ring / smartphone / other |
| latitude | Registered location — full precision |
| longitude | Registered location — full precision |
| location_name | Human-readable place name |
| active | Boolean |
| created_at | Registration timestamp |

---

## Camera & media ingestion

### Supported camera types (initial)
| Camera | Connection | Media |
|--------|-----------|-------|
| Reolink Argus series | FTP/SFTP (next sprint) | JPEG, MP4 |
| Smartphone (Android/iOS) | Direct upload | JPEG |
| Ring | Manual export | MP4 |

### Ingestion pipeline
1. Media arrives (upload or FTP pickup)
2. Validate file type and size
3. Extract EXIF metadata — timestamp, GPS, device ID
4. If video: extract representative frame(s) as JPEG using ffmpeg
5. Determine geolocation: EXIF GPS → camera location → account default → none
6. Queue for detection
7. Detection service processes frame
8. Result written to database with status `pending`
9. Appears in participant's verification queue

---

## AI detection pipeline

### Full pipeline (with MegaDetector)
1. MegaDetector runs on frame → finds animal bounding boxes
2. If no animals found → mark as `empty`, skip SpeciesNet
3. Best animal bounding box passed to SpeciesNet
4. SpeciesNet classifies with geolocation ensemble
5. Result returned with species, confidence, detector attribution

### Geolocation ensemble
- Pass country_code and admin1_region to SpeciesNet ensemble
- Improves species disambiguation for Australian fauna
- Currently hardcoded to AUS/Western Australia
- Sprint 4: read from EXIF or camera location

---

## Web interface

### Participant view

**Dashboard**
- Quick stats: total detections, verified, pending review, unique species
- Species over time chart (last 7 days default, selectable: 7d/30d/all time)
- Species composition donut chart (top 8 species + other)
- Activity by time of day histogram (24h)
- Charts use verified detections only (except activity histogram)

**Detection feed**
- Browse detections filtered by species, date, camera, status, confidence
- Detection card: still image + "▶ Play video" if sourced from video
- Status badge: pending / verified / rejected / reprocessing
- Detector badge showing which AI made the prediction
- Empty frame detections shown greyed out
- Confidence threshold filter

**Verification queue**
- Pending count badge in header — clickable, jumps to pending filter
- Review modal:
  - Large extracted frame
  - Video player if detection sourced from video
  - AI prediction: species, scientific name, confidence bar
  - Detector attribution badge
  - Actions: Confirm / Correct / Re-run / Reject

**Camera management (future sprint)**
- Register cameras with location
- View camera status, last upload
- Set default geolocation per camera

### Public/community view
- Aggregated species occurrence map (RASD obfuscated)
- Species occurrence over time
- Species composition
- Wildlife highlights feed — curated verified video detections

---

## Data export & integration (future sprint)
- ALA — Darwin Core occurrence records
- BDR — quarterly ingest
- iNaturalist — optional cross-posting per participant
- Only verified records exported

---

## Multi-tenancy & accounts (future sprint)
- User registration and authentication
- Camera registration with location
- Data ownership — participant owns raw data
- Licence per account (CC0 or CC-BY)
- Privacy controls — opt-in to public aggregation

---

## Tech stack
| Component | Technology |
|-----------|-----------|
| Backend | Python / FastAPI |
| Database | PostgreSQL |
| Queue | RabbitMQ (future — detection currently synchronous) |
| Media storage | Local filesystem (prototype), S3-compatible (production) |
| Frontend | React / Vite |
| Charts | Recharts |
| Detectors | Independent microservices, standard REST interface |
| Containers | Docker Compose |
| Hosting | Hetzner CX23 |
| Domain | wombat.watch |
| CDN/DNS | Cloudflare |
| SSL | Let's Encrypt |
| Source control | GitHub — grant-malcolm/wombat-platform |
| Licence | MIT |

---

## Standards alignment
- Darwin Core — occurrence record schema
- RASD framework — location sensitivity and obfuscation
- CC0 / CC-BY — data licensing
- SRID 4326 (WGS84) — coordinate system

---

## Sprint history

### Sprint 1 — Walking skeleton ✅
Upload → frame extraction → placeholder detection → React UI

### Sprint 2 — SpeciesNet + verification queue ✅
SpeciesNet microservice, detector registry, verification queue UI, status badges

### Sprint 3 — MegaDetector + dashboard (in progress)
MegaDetector microservice, geolocation, analytics dashboard, UI polish

### Sprint 4 — Geolocation from EXIF + camera registration (planned)
EXIF GPS extraction, camera registration with location, location inheritance pipeline

### Future sprints
- FTP/SFTP camera ingestion (Reolink)
- Multi-user accounts
- RASD-compliant location obfuscation
- ALA and BDR export
- iNaturalist cross-posting
- Public community view
- Mobile PWA
