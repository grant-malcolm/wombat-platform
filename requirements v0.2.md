WOMBAT Platform Requirements v0.2
Vision
A citizen science wildlife monitoring platform for Australia. Participants deploy cameras, the platform handles AI species detection, and the aggregated data contributes to national biodiversity science. Public engagement through video and beautiful visualisation; hard science through standards-compliant data export.

Architecture principles
Pluggable detector registry

Each detector implements a standard interface: image in → species prediction out
Detectors run as independent microservices behind a common API contract
Account owners can select preferred detector per project
Multiple detectors can be run on same media for comparison
New detectors can be added without changing core platform

Initial detectors:

SpeciesNet v4 (Google/Addax Data Science)
DeepFaune (CNRS) — already in AddaxAI Connect
Placeholder (random Australian species — testing only)

Future detectors:

iNaturalist Computer Vision API
Additional models as they emerge

Human-in-the-loop verification
AI provides first cut, humans verify before science export. Inspired by MATE's QA workflow.

Data model
Detection record
FieldDescriptionidUUIDmedia_idLink to source image or videoframe_idLink to extracted frame (if video)detector_idWhich detector made this predictiondetected_speciesCommon name from detectordetected_species_scientificScientific name from detectorconfidenceConfidence score 0-1statuspending / verified / rejected / reprocessingverified_byUser who verified (nullable)verified_atTimestamp of verification (nullable)verified_speciesHuman-confirmed species (may differ from detected)verified_species_scientificHuman-confirmed scientific namenotesReviewer notescreated_atDetection timestamp
Media record
FieldDescriptionidUUIDcamera_idSource cameramedia_typeimage / videooriginal_filenameAs uploadedstored_pathInternal storage pathcaptured_atTimestamp from EXIF or filenamelatitudeFull precision (internal only)longitudeFull precision (internal only)datumCoordinate datumlicenceCC0 / CC-BY per participant setting
Location display rules (RASD-aligned)
Species sensitivityDisplay precisionSensitive10km gridNear-sensitive1km gridGeneralExact (or minimal obfuscation)
Full coordinates always stored internally. Obfuscation applied at display/export layer only.

Camera & media ingestion
Supported camera types (initial)
CameraConnectionMediaReolink Argus seriesFTP/SFTPJPEG, MP4Smartphone (Android/iOS)Direct uploadJPEGRingManual exportMP4
Pipeline

Media arrives (upload or FTP pickup)
Validate file type and size
Extract EXIF metadata (timestamp, GPS, device ID)
If video: extract representative frame(s) as JPEG
Queue for detection
Detection service processes frame
Result written to database with status pending
Appears in participant's verification queue


Web interface
Participant view
Dashboard

My cameras, recent detections, species seen this week
Quick stats: total detections, verified, pending review

Detection feed

Browse all detections filtered by species, date, camera, status
Detection card: still image + "▶ Play video" if sourced from video
Location shown at obfuscated precision appropriate to species

Verification queue

List of detections with status pending
Each item shows: extracted frame, detector prediction, confidence score
Actions per detection:

✅ Confirm — mark as verified, species confirmed
✏️ Correct — enter correct species manually, mark verified
🔄 Re-run — select different detector and reprocess
❌ Reject — not a valid detection (empty frame, false trigger)


Bulk actions for high-volume users

Camera management

Register cameras, assign to projects
View camera status, last upload, battery warnings

Public/community view

Aggregated species occurrence map (obfuscated per RASD)
Species occurrence over time (charts)
Species composition charts
Hotspot visualisation
"Wildlife highlights" — curated verified video detections


Analytics dashboard

Species occurrence over time (line/bar charts)
Species composition by camera/project (pie/donut)
Detection confidence distribution
Verification rate and backlog
Activity heatmap by time of day


Data export & integration

ALA — periodic occurrence record submission, Darwin Core format
BDR — quarterly ingest, Darwin Core format
iNaturalist — optional cross-posting of verified detections per participant
RASD service — aligned with national framework, potential data provider status
Only verified records exported to external services


Multi-tenancy & accounts

User registration and authentication
Role-based access: participant, reviewer, admin
Camera registration per user
Project-based organisation (one user, multiple projects)
Data ownership — participant owns raw data
Licence recorded at account level (CC0 or CC-BY)
Privacy controls — opt-in to public aggregation


Location privacy

Full coordinates stored internally, never exposed via API without authorisation
Display precision governed by species sensitivity (RASD framework)
Participant can always see their own exact data
Public aggregated view always obfuscated


Prototype scope (current sprint)
Done ✅

Walking skeleton — upload, frame extraction, placeholder detection, React UI
Video support — Ring MP4 tested and working
Deployed to https://wombat.watch
Boot resilience — containers start automatically on server reboot

Next sprint

 SpeciesNet microservice — real AI detection replacing placeholder
 Detector registry — pluggable architecture, SpeciesNet as first real detector
 Verification queue — human review workflow
 Updated data model — status, verified fields, detector reference
 Mobile responsive UI

Future sprints

 FTP/SFTP camera ingestion (Reolink)
 Multi-user / camera registration
 RASD-compliant location obfuscation
 Analytics dashboard
 ALA and BDR export (Darwin Core)
 iNaturalist cross-posting


Tech stack

Backend: Python / FastAPI
Database: PostgreSQL
Queue: RabbitMQ (next sprint — detection moves off request thread)
Media storage: Local filesystem (prototype), S3-compatible (production)
Frontend: React
Detectors: Independent microservices behind standard API contract
Containers: Docker Compose
Hosting: Hetzner CX23, wombat.watch
Source control: GitHub — github.com/grant-malcolm/wombat-platform
Licence: MIT


Standards alignment

Darwin Core — occurrence record schema
RASD framework — location sensitivity and obfuscation
CC0 / CC-BY — data licensing
SRID 4326 (WGS84) — coordinate system
