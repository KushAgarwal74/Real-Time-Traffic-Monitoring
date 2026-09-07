🚦 Real-Time Traffic Monitoring System

An end-to-end real-time traffic monitoring and analytics pipeline combining Computer Vision, Apache Kafka, TimescaleDB, GPS telemetry, and Grafana.

The system processes traffic video, detects and tracks vehicles using YOLO + ByteTrack, generates structured vehicle lifecycle events, synchronizes events with camera GPS telemetry, streams events through Apache Kafka, persists them in TimescaleDB, and visualizes traffic activity through a Grafana Geomap dashboard.

License-plate detection and OCR are implemented as optional enrichment and are intentionally separated from the core traffic-event pipeline.

🏷️ Tech Stack








✨ Features

🎥 Video-based vehicle detection using YOLO

🆔 Persistent multi-object tracking using ByteTrack

🚗 Vehicle classification:

Car

Motorcycle

Bus

Truck

📡 Video-frame to GPX/GPS timestamp synchronization

🧭 Camera latitude/longitude attached to traffic events

📨 Real-time event streaming through Apache Kafka

💾 Time-series event storage using TimescaleDB

🗺️ Grafana Geomap with:

OpenStreetMap basemap

GPS Route layer

Vehicle-event markers

Vehicle-type marker coloring

📄 JSONL event backup for replay and debugging

🔎 Optional license-plate detection and OCR

🐳 Local infrastructure managed with Docker Compose

📸 Dashboard Preview

The Grafana dashboard visualizes the camera trajectory and traffic events geographically.

Add your final Grafana dashboard screenshot here

Suggested file:
docs/images/grafana-dashboard.png

![Grafana Traffic Monitoring Dashboard](docs/images/grafana-dashboard.png)

🏗️ Architecture

                         ┌──────────────────────┐
                         │    Traffic Video     │
                         │       / Camera       │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │     VideoRunner      │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   TrafficPipeline    │
                         └──────────┬───────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
       ┌──────────────┐      ┌──────────────┐     ┌─────────────────┐
       │ GPS / GPX    │      │ YOLO +       │     │ License Plate   │
       │ Synchronizer │      │ ByteTrack    │     │ Enrichment      │
       └──────┬───────┘      └──────┬───────┘     │ (Optional)      │
              │                     │             └────────┬────────┘
              └─────────────────────┼──────────────────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    Traffic Events    │
                         │                      │
                         │ vehicle_detected     │
                         │ vehicle_updated      │
                         │ vehicle_exited       │
                         └──────────┬───────────┘
                                    │
                       ┌────────────┴────────────┐
                       │                         │
                       ▼                         ▼
              ┌─────────────────┐       ┌─────────────────┐
              │   events.jsonl  │       │ Apache Kafka    │
              │ Backup / Replay │       │ traffic-events  │
              └─────────────────┘       └────────┬────────┘
                                                  │
                                                  ▼
                                        ┌─────────────────┐
                                        │ Kafka Consumer  │
                                        └────────┬────────┘
                                                 │
                                                 ▼
                                        ┌─────────────────┐
                                        │   TimescaleDB   │
                                        │ traffic_events  │
                                        └────────┬────────┘
                                                 │
                                                 ▼
                                        ┌─────────────────┐
                                        │     Grafana     │
                                        │ Geomap + KPIs   │
                                        └─────────────────┘

🔄 End-to-End Data Flow

1. Video Processing

VideoRunner reads the input video frame-by-frame and passes each frame to TrafficPipeline.

For each frame, the pipeline:

Calculates the frame timestamp.

Synchronizes the frame with GPX telemetry.

Retrieves the camera latitude/longitude.

Runs YOLO vehicle detection.

Tracks vehicles using ByteTrack.

Updates vehicle state.

Generates traffic events.

Optionally performs license-plate enrichment.

2. GPS / GPX Synchronization

Video frame
     │
     ▼
Frame number + FPS
     │
     ▼
Video timestamp
     │
     ▼
GPX timestamp
     │
     ▼
Camera latitude / longitude

The GPS position stored with an event represents the camera/recording device position at that event timestamp.

Important: camera_gps is not an individual vehicle GPS location. The Geomap markers therefore represent traffic events observed while the camera was at that location.

🚗 Vehicle Detection & Tracking

The computer-vision pipeline uses:

Component

Purpose

YOLO

Vehicle detection and classification

ByteTrack

Persistent object tracking

Vehicle State Manager

Maintains vehicle lifecycle state

Supported vehicle categories currently observed:

car
motorcycle
truck
bus

Each tracked vehicle receives a persistent track_id, allowing the system to associate observations across frames.

📡 Traffic Events

The pipeline produces vehicle lifecycle events such as:

vehicle_detected
vehicle_updated
vehicle_exited

A representative event looks like:

{
  "frame_number": 1234,
  "timestamp": "2026-09-01T08:27:30.621952+00:00",
  "event_type": "vehicle_detected",
  "track_id": 3128,
  "vehicle_type": "car",
  "confidence": 0.91,
  "camera_gps": {
    "latitude": 18.494081377078402,
    "longitude": 73.94783292973824,
    "elevation": 500.0,
    "timestamp": "2026-09-01T08:27:30.621952+00:00"
  }
}

License-plate fields are optional and depend on the enrichment result.

📨 Apache Kafka

Traffic events are published to:

traffic-events

Kafka provides the streaming boundary between the computer-vision pipeline and downstream consumers.

TrafficPipeline
      │
      ▼
Kafka Producer
      │
      ▼
traffic-events
      │
      ▼
Kafka Consumer
      │
      ▼
TimescaleDB

The local Kafka setup uses KRaft mode and does not require the older ZooKeeper architecture.

Kafka UI is available locally for inspecting topics, partitions, messages, and consumer activity.

💾 TimescaleDB

Traffic events are stored in the traffic_events hypertable.

Core fields include:

Field

Description

id

Event identifier

event_time

Event timestamp

event_type

Vehicle lifecycle event

track_id

Persistent tracking ID

vehicle_type

Car, motorcycle, bus, or truck

confidence

Detection confidence

bbox

Vehicle bounding box

camera_gps

Camera GPS telemetry

license_plate

Optional recognized plate

plate_confidence

Optional plate confidence

raw_event

Original event payload

Example aggregation:

SELECT
    vehicle_type,
    COUNT(*) AS count
FROM traffic_events
WHERE vehicle_type IS NOT NULL
GROUP BY vehicle_type
ORDER BY count DESC;

Current dataset example:

car          893
motorcycle   543
truck        312
bus           94

🗺️ Grafana Dashboard

The project includes a Grafana dashboard connected to TimescaleDB.

Geomap

OpenStreetMap
      │
      ├── Route Layer
      │      └── Camera GPS trajectory
      │
      └── Marker Layer
             └── Traffic events

Vehicle markers are color-coded by vehicle_type:

🔵 Motorcycle
🟢 Car
🟠 Bus
🔴 Truck

The marker layer can expose fields such as:

vehicle_type
track_id
event_type
confidence
license_plate
event_time

The dashboard can also include:

Total traffic events

Vehicle counts by type

Traffic events over time

Vehicle distribution

Camera route and traffic-event locations

📁 Project Structure

Real-Time-Traffic-Monitoring/
│
├── cv_pipeline/
│   ├── traffic_pipeline.py
│   ├── traffic_tracker.py
│   ├── vehicle_plate_pipeline.py
│   ├── license_plate_detector.py
│   ├── license_plate_ocr.py
│   ├── plate_validator.py
│   ├── plate_ocr_validator.py
│   ├── plate_ocr_aggregator.py
│   └── vehicle_state_manager.py
│
├── producers/
│   ├── run_traffic_video.py
│   ├── video_runner.py
│   └── kafka_producer.py
│
├── consumers/
│   └── kafka_consumer.py
│
├── kafka/
│   ├── docker-compose.yml
│   └── init.sql
│
├── gps/
│   ├── gpx_parser.py
│   ├── synchronizer.py
│   └── video_gps_sync.py
│
├── database/
│   └── init.sql
│
├── data/
│   ├── raw/
│   │   ├── city/
│   │   └── gps/
│   └── processed/
│
├── models/
│
├── outputs/
│   └── videos/
│
├── docs/
│   └── images/
│
├── requirements.txt
├── .gitignore
└── README.md

🚀 Getting Started

Prerequisites

Docker Desktop

Python 3.x

Git

Make sure Docker Desktop is running before starting the infrastructure.

1. Clone the Repository

git clone <YOUR_REPOSITORY_URL>
cd Real-Time-Traffic-Monitoring

2. Start Infrastructure

docker compose up -d

Verify the containers:

docker ps

Expected services:

kafka-local
kafka-ui-local
timescaledb-local
grafana-local

3. Create a Python Virtual Environment

python3 -m venv .venv
source .venv/bin/activate

Install dependencies:

pip install -r requirements.txt

▶️ Run the Traffic Pipeline

Current example input:

data/raw/city/traffic_1.mp4

GPS telemetry:

data/raw/gps/traffic_1.gpx

Run:

python producers/run_traffic_video.py

The pipeline produces:

outputs/videos/traffic_1_output.mp4
data/processed/traffic_1/events.jsonl
data/processed/traffic_1/summary.json

At the same time, traffic events are published to:

traffic-events

🔎 Inspect Kafka

Kafka UI:

http://localhost:8080

Kafka broker:

localhost:9092

Use Kafka UI to inspect:

Topics

Partitions

Messages

Consumer activity

📊 Access Grafana

Grafana:

http://localhost:3000

Local development credentials configured for the project:

Username: admin
Password: admin

Change the default password before exposing Grafana outside a local development environment.

🗄️ TimescaleDB Connection

Local connection parameters:

Host:     localhost
Port:     5432
Database: traffic_db
User:     traffic_user
Password: traffic_password

For the Grafana PostgreSQL datasource, use the Docker Compose service name:

timescaledb:5432

because Grafana and TimescaleDB run on the same Docker Compose network.

🗺️ Geomap Query

The marker layer extracts camera coordinates from camera_gps:

SELECT
    event_time AS "time",
    (camera_gps->>'latitude')::double precision AS latitude,
    (camera_gps->>'longitude')::double precision AS longitude,
    event_type,
    track_id,
    vehicle_type,
    confidence,
    license_plate
FROM traffic_events
WHERE
    camera_gps IS NOT NULL
    AND camera_gps->>'latitude' IS NOT NULL
    AND camera_gps->>'longitude' IS NOT NULL
    AND $__timeFilter(event_time)
ORDER BY event_time;

Geomap configuration:

Location Mode: Coords
Latitude:      latitude
Longitude:     longitude

🧪 Verification

Check traffic-event count

SELECT COUNT(*)
FROM traffic_events;

Check vehicle distribution

SELECT
    vehicle_type,
    COUNT(*) AS count
FROM traffic_events
WHERE vehicle_type IS NOT NULL
GROUP BY vehicle_type
ORDER BY count DESC;

Check GPS availability

SELECT
    event_time,
    event_type,
    track_id,
    camera_gps
FROM traffic_events
WHERE camera_gps IS NOT NULL
ORDER BY event_time DESC
LIMIT 20;

Check event types

SELECT
    event_type,
    COUNT(*) AS count
FROM traffic_events
GROUP BY event_type
ORDER BY count DESC;

🔎 License Plate Detection & OCR

License-plate processing is implemented as an optional enrichment pipeline:

Vehicle
   │
   ▼
Plate Detector
   │
   ▼
Plate Validator
   │
   ▼
OCR
   │
   ▼
OCR Validator
   │
   ▼
Plate Aggregator
   │
   ▼
Traffic Event

OCR is intentionally not required for the core traffic-monitoring pipeline.

The primary system path is:

Video
  ↓
Detection
  ↓
Tracking
  ↓
Traffic Events
  ↓
Kafka
  ↓
TimescaleDB
  ↓
Grafana

Plate recognition can be improved independently without changing the core streaming architecture.

📈 Example Analytics

Events per minute

SELECT
    time_bucket('1 minute', event_time) AS time,
    COUNT(*) AS traffic_events
FROM traffic_events
WHERE $__timeFilter(event_time)
GROUP BY time
ORDER BY time;

Vehicle distribution

SELECT
    vehicle_type,
    COUNT(*) AS vehicle_count
FROM traffic_events
WHERE
    vehicle_type IS NOT NULL
    AND $__timeFilter(event_time)
GROUP BY vehicle_type
ORDER BY vehicle_count DESC;

🛠️ Technology Stack

Component

Technology

Language

Python

Computer Vision

OpenCV

Object Detection

YOLO

Object Tracking

ByteTrack

Streaming

Apache Kafka

Kafka Client

Confluent Kafka

Database

PostgreSQL + TimescaleDB

GPS

GPX telemetry

Visualization

Grafana

Map

OpenStreetMap

Infrastructure

Docker / Docker Compose

Event Backup

JSONL

🎯 Engineering Goals

This project demonstrates an end-to-end engineering workflow rather than only an object-detection model.

Process traffic video with computer vision.

Maintain vehicle identities across frames.

Generate structured vehicle lifecycle events.

Synchronize events with camera GPS telemetry.

Stream events through Apache Kafka.

Persist events in a time-series database.

Query and aggregate traffic data.

Visualize traffic activity geographically and temporally.

Keep optional ML enrichment components decoupled from the core streaming pipeline.

🔮 Roadmap

Real-time camera streams instead of prerecorded video

Multiple camera sources

Kafka partitioning by camera ID

Vehicle speed estimation

Traffic-density estimation

Congestion detection

Lane-level analytics

Direction-of-travel analysis

Vehicle dwell-time analytics

Improved license-plate OCR

Grafana alerting

Dashboard auto-refresh

Production Kafka deployment

Containerized CV workers

Cloud deployment

Historical traffic analytics

📌 Project Status

Component

Status

YOLO vehicle detection

✅ Working

ByteTrack tracking

✅ Working

Vehicle lifecycle events

✅ Working

GPX/video synchronization

✅ Working

Camera GPS in events

✅ Working

Kafka producer

✅ Working

traffic-events topic

✅ Working

Kafka consumer

✅ Working

TimescaleDB

✅ Working

Traffic event persistence

✅ Working

Grafana PostgreSQL datasource

✅ Working

Grafana Geomap

✅ Working

OpenStreetMap basemap

✅ Working

GPS Route layer

✅ Working

Vehicle-colored markers

✅ Working

Marker tooltip

🔧 Dashboard configuration

KPI dashboard

🔧 In progress

Advanced OCR

🔮 Future improvement

🤝 Development

For collaborative development:

git checkout -b feature/your-feature

Make your changes, commit them, and open a Pull Request.

Avoid pushing experimental changes directly to main or master.

Large binary assets such as:

*.mp4
*.pt
*.onnx

should generally remain outside Git and be managed through the project's .gitignore and appropriate data/model storage.

🔐 Security Notes

The credentials in this README are intended for local development only.

Before deploying outside a local environment:

Change Grafana's default password.

Use environment variables or secrets for database credentials.

Do not commit credentials to Git.

Do not commit large/private video or model assets unless intentionally required.

Review .gitignore before the first push.

👤 Project Focus

The project is intentionally structured around a complete:

Computer Vision
      ↓
Traffic Events
      ↓
Apache Kafka
      ↓
Kafka Consumer
      ↓
TimescaleDB
      ↓
Grafana
      ↓
Geospatial + Time-Series Analytics

The architecture provides a foundation that can evolve from a local video-processing prototype into a multi-camera real-time traffic analytics platform.