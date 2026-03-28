WOMBAT 🦘
Wildlife Observation and Monitoring with Biodiversity Aggregation Technology
WOMBAT is an open-source citizen science platform for automated wildlife monitoring across Australia. Point a camera at your backyard, bush block, or farm — WOMBAT handles the rest.
What it does

Ingests images and video from supported wildlife cameras via FTP/SFTP or direct upload
Detects animals using MegaDetector
Identifies species using SpeciesNet
Stores detection stills and source video so you can watch animal behaviour, not just see a label
Visualises species occurrences over time, across space, and by composition
Aggregates data from distributed camera networks into a shared searchable dataset
Exports occurrence records in Darwin Core format to the Atlas of Living Australia and the Biodiversity Data Repository

Why WOMBAT
Existing wildlife camera platforms assume cameras produce still images. WOMBAT is built for the reality that modern cameras — including consumer devices like Reolink and Ring — produce video. The detection pipeline extracts frames for AI analysis, but the source video is always stored and playable. Watching a quenda forage or a quoll hunt is the hook that drives participation. The science happens in the background.
Key features

🎥 Video-first — stills for detection, video for engagement
🗺️ Spatial mapping — occurrence hotspots with RASD-compliant location obfuscation for sensitive species
📊 Analytics dashboard — species occurrence over time, composition charts, activity patterns
🔒 Privacy by design — full coordinates stored internally, display precision governed by species sensitivity following the RASD framework
🌏 Australia-wide — designed for Australian fauna and aligned with national biodiversity data infrastructure
👥 Multi-user — participants register cameras, own their data, and choose their sharing licence (CC0 or CC-BY)
🔌 Open source — MIT licensed, built to be contributed to

Supported cameras
CameraConnectionMediaReolink Argus seriesFTP/SFTPJPEG, MP4Smartphone (Android/iOS)Direct uploadJPEGRingManual exportMP4
More camera types will be added. Contributions welcome.
Tech stack

Backend: Python / FastAPI
Database: PostgreSQL
Queue: RabbitMQ
Media storage: S3-compatible object storage
Frontend: React
AI pipeline: MegaDetector + SpeciesNet
Containers: Docker Compose

Status
🚧 Early prototype — actively under development.
This is a proof of concept being developed to demonstrate the viability of a national citizen science wildlife video monitoring platform. We are actively seeking collaborators and institutional support.
Roadmap

 Walking skeleton — upload → detect → display
 Video support with linked still/video detections
 Multi-camera ingestion (Reolink, smartphone)
 Occurrence mapping with RASD obfuscation
 Analytics dashboard
 Multi-user / camera registration
 ALA and BDR export
 iNaturalist cross-posting

Contributing
Contributions are welcome. If you're interested in contributing or would like to discuss the project please open an issue or get in touch.
Acknowledgements
WOMBAT builds on MegaDetector by Dan Morris and SpeciesNet by Google. Location sensitivity guidance follows the RASD framework developed by the Atlas of Living Australia and partners.
Licence
MIT

# wombat-platform

Point a camera at your backyard, bush block, or farm. We handle the rest — species detection, mapping, aggregation. Watch your footage. Share your data. Contribute to Australian biodiversity science.
