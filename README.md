# Real-Time Traffic Monitoring System (YOLO + Apache Kafka)

# 🚦 Real-Time Traffic Monitoring System

An end-to-end **real-time traffic monitoring system** built using Computer Vision, Apache Kafka, and TimescaleDB.

The system detects and tracks vehicles from traffic video streams, detects license plates, performs OCR, generates traffic events, streams them through Kafka, and stores them in TimescaleDB for downstream analytics and dashboard visualization.

---

# 🏗️ System Architecture

```text
                    ┌─────────────────────┐
                    │   Traffic Video     │
                    │    / Camera Feed    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Video Runner      │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Traffic Pipeline   │
                    └──────────┬──────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
            ▼                  ▼                  ▼
     Vehicle Detection     Tracking        License Plate
        + Tracking                         Detection + OCR
            │                  │                  │
            └──────────────────┼──────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Traffic Events    │
                    │                     │
                    │ vehicle_detected    │
                    │ vehicle_updated     │
                    │ vehicle_exited      │
                    └──────────┬──────────┘
                               │
                 ┌─────────────┴─────────────┐
                 │                           │
                 ▼                           ▼
        ┌─────────────────┐         ┌─────────────────┐
        │   events.jsonl  │         │      Kafka      │
        │  Backup / Replay│         │  traffic-events │
        └─────────────────┘         └────────┬────────┘
                                             │
                                             ▼
                                    ┌─────────────────┐
                                    │ Kafka Consumer  │
                                    └────────┬────────┘
                                             │
                                             ▼
                                    ┌─────────────────┐
                                    │   TimescaleDB   │
                                    └────────┬────────┘
                                             │
                                             ▼
                                    ┌─────────────────┐
                                    │    Dashboard    │
                                    │   (Planned)     │
                                    └─────────────────┘

A distributed, real-time data streaming pipeline that processes video frames using computer vision (YOLO) and orchestrates telemetry payloads using Apache Kafka stream processing topologies.

  [ Video / Camera Stream ] 
             │
             ▼
 1. PRODUCERS (mock_producer.py) 
    - Runs your YOLO model on raw video frames.
    - Detects counts (e.g., "cars: 12", "trucks: 2").
    - Pushes this metadata (JSON) to Kafka.
             │
             ▼
       [ Kafka Broker ] (via docker-compose.yml)
             │
             ▼
 2. STREAMS APP (main.py)
    - Consumes the raw vehicle counts.
    - Aggregators calculate traffic density windows (e.g., "Average cars/min").
    - Processors filter alerts (e.g., "If speed == 0 for 5 mins, flag traffic jam").
             │
             ▼
 3. CONSUMERS (dashboard_sink.py)
    - Reads the processed insights, windowed averages, or alerts.
    - Saves them to a database or pushes them to a frontend UI map dashboard.

---

## 🏗️ Core Architecture Blueprint
1. **Producers (`producers/`):** Feeds live video camera arrays to a YOLO inference model to output text JSON frame metadata to a target event pipeline topic.
2. **Cluster Infrastructure (`docker-compose.yml`):** Deploys isolated ZooKeeper coordination nodes, a central Apache Kafka broker cluster instance, and a Kafka-UI analytics tracking plane.
3. **Streams Engine (`streams_app/`):** Ingests raw telemetry tracking arrays to calculate sliding time windows, lane counts, and bottleneck alerts.
4. **Consumers (`consumers/`):** Acts as the final streaming database sink node to feed user charts or map dashboards.

---

## 📋 Initial Verification Logs & Test History
The initial local pipeline infrastructure was successfully tested and verified on a Mac mini using a Python virtual environment connected to local Docker containers.

### 1. Verification Commands Executed
```bash
# Step A: Cleaned storage caches and booted all 3 infrastructure containers
docker compose down -v && docker compose up -d

# Step B: Initialized and toggled an isolated workspace sandbox layer
python3 -m venv .venv
source .venv/bin/activate

# Step C: Synchronized pipeline libraries
pip install --upgrade pip
pip install confluent-kafka

# Step D: Launched the engine analyzer consumer node (Terminal 1)
python streams_app/main.py

# Step E: Triggered the YOLO matrix simulation stream feed (Terminal 2)
python producers/mock_producer.py
```

### 2. Confirmed Cluster Output Logs
During live communication testing, the pipeline passed continuous metadata exchanges through Partition 0 without losing tracking frames:

#### 📁 Terminal 1 Ingestion Logs (`producers/mock_producer.py`)
```text
[*] Starting mock YOLO camera stream... Press Ctrl+C to terminate.
[+] YOLO Frame data sent to topic: traffic-raw-data [Partition: 0]
[+] YOLO Frame data sent to topic: traffic-raw-data [Partition: 0]
[+] YOLO Frame data sent to topic: traffic-raw-data [Partition: 0]
[+] YOLO Frame data sent to topic: traffic-raw-data [Partition: 0]
^C
[*] Stopping producer feed gracefully...
```

#### 📁 Terminal 2 Processing Engine Logs (`streams_app/main.py`)
```text
[*] Kafka Stream Engine active. Awaiting logs from YOLO node...
[Engine Output] Loc: intersection_north_highway | Frame: 91 | Counted Vehicles: 15 -> Breakdown: {'car': 8, 'truck': 2, 'bus': 1, 'motorcycle': 4}
[Engine Output] Loc: intersection_north_highway | Frame: 92 | Counted Vehicles: 15 -> Breakdown: {'car': 8, 'truck': 2, 'bus': 1, 'motorcycle': 4}
[Engine Output] Loc: intersection_north_highway | Frame: 93 | Counted Vehicles: 15 -> Breakdown: {'car': 8, 'truck': 2, 'bus': 1, 'motorcycle': 4}
^C
[*] Stopping engine stream consumer...
```

---

## 🚀 Teammate Onboarding & Local Setup

### 1. Provision Cluster Components
Ensure **Docker Desktop** is active on your host system, open your terminal at the project root directory, and type:
```bash
docker compose up -d
```
*   **Web Dashboard UI Manager:** [http://localhost:8080](http://localhost:8080)
*   **Kafka Cluster Bootstrap URL:** `localhost:9092`

### 2. Configure Your Isolated Python Workspace
```bash
source .venv/bin/activate
pip install -r producers/requirements.txt
```

---

## 🎯 Shared Group Commit Protocol & Roles
*   **Branch Isolation Rules:** Do not push updates directly to `main` or `master`. Always perform atomic checkouts (`git checkout -b feature/your-task`) and open an explicit Pull Request for evaluation.
*   **Storage Boundaries:** Because your `.gitignore` explicitly filters out `*.pt`, `*.onnx`, and binary text `*.mp4` assets, model data will remain safely outside GitHub system thresholds.

### Project Folders Ownership Matrix
*   **Teammates 1 & 2 (Computer Vision):** Manage `producers/` configurations to run live YOLO classification routines inside `mock_producer.py`.
*   **Teammates 3 & 4 (Analytics Framework):** Code windowed stream aggregation scripts in `streams_app/processors.py` and `aggregators.py`.
*   **Teammate 5 (Storage Core):** Connect `consumers/dashboard_sink.py` to target data collection engines or live dashboard platforms.
