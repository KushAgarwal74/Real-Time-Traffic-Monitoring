# Real-Time Traffic Monitoring System (YOLO + Apache Kafka)

# 🚦 Real-Time Traffic Monitoring System

An end-to-end **real-time traffic monitoring system** built using Computer Vision, Apache Kafka, and TimescaleDB.

The system detects and tracks vehicles from traffic video streams, detects license plates, performs OCR, generates traffic events, streams them through Kafka, and stores them in TimescaleDB for downstream analytics and dashboard visualization.

---

# 🏗️ System Architecture

```text
MP4 video + GPX metadata
          |
          v
producers/run_traffic_video.py
          |
          v
cv_pipeline/traffic_pipeline.py
          |
          +--> Vehicle detection and tracking
          +--> License-plate detection and OCR
          +--> GPS/timestamp synchronization
          |
          v
producers/video_runner.py
          |
          +--> Annotated MP4
          +--> events.jsonl and summary.json
          +--> Kafka topic: traffic-events
                                      |
                                      v
                           consumers/traffic_consumer.py
                                      |
                                      v
                           TimescaleDB: traffic_events
                                      |
                         +------------+------------+
                         |                         |
                    pgAdmin 4                 Grafana
                                                   |
                                      Dashboard configuration
```

The main application path is:

```text
MP4 + GPX -> CV pipeline -> Kafka -> TimescaleDB
                  |
                  +-> annotated video and local JSON files
```

The separate `streams_app/` example consumes mock vehicle-count messages from
the `traffic-raw-data` topic. It is not an intermediate stage in the MP4
processing path.

## Core Architecture Components

1. **Video entry point (`producers/run_traffic_video.py`):** Uses the sample
   MP4, matching GPX file, and license-plate model defaults.
2. **Computer vision (`cv_pipeline/`):** Synchronizes GPS metadata, tracks
   vehicles, detects plates, performs OCR, and emits vehicle lifecycle events.
3. **Video runner (`producers/video_runner.py`):** Writes annotated video and
   JSON backups, and publishes events to Kafka.
4. **Kafka (`kafka/docker-compose.yml`):** Runs Apache Kafka in KRaft mode,
   Kafka UI, TimescaleDB, and Grafana. Host clients use `localhost:9092`.
5. **Database consumer (`consumers/traffic_consumer.py`):** Reads
   `traffic-events` and inserts rows into the `traffic_events` hypertable.
6. **Storage and visualization:** TimescaleDB stores events; pgAdmin 4 can
   query them; Grafana is available but not automatically provisioned with a
   datasource or dashboard.

## Grafana provisioning & local execution (quick guide)
- Provisioning files live under: kafka/provisioning/
 - Datasources: kafka/provisioning/datasources/datasources.yml
 - Alert rules: kafka/provisioning/alerting/rules/*.yaml (e.g. vehicle-count-above-100.yaml)

- Run locally (recommended: baked image)
 1. Edit datasource values if needed: kafka/provisioning/datasources/datasources.yml (database/user/password/url).
 2. Build and start Grafana with baked provisioning so files are copied into the image:
    cd kafka
    docker-compose -f docker-compose.yml up -d --build grafana

- Apply without rebuilding (temporary):
    docker cp kafka/provisioning/alerting/rules/vehicle-count-above-100.yaml grafana-local:/etc/grafana/provisioning/alerting/rules/ && docker restart grafana-local

- If you prefer an editable datasource in the UI for testing, create one in Grafana (name: timescaledb-local) or create via API. The dashboard JSON in the repo has been updated to reference "timescaledb-local" (uid ffy0ik8xil7nkb).

- Verify after start: http://localhost:3000 → Configuration → Data sources; Alerting → Alert rules; Dashboards → Real-Time Traffic & License Plate Monitoring



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

## 🚀 Local Application Testing

Ensure **Docker Desktop** is running before starting the test.

The video/GPS synchronization step requires the native FFmpeg tools. On macOS,
install them with Homebrew if `ffprobe` is not already available:

```bash
brew install ffmpeg
ffprobe -version
```

The license-plate model files are stored with Git LFS. Install Git LFS and
download the model weights before running the video pipeline:

```bash
brew install git-lfs
git lfs install
git lfs pull --include="models/*.pt"
```

### 1. Start Kafka and TimescaleDB

Run Docker Compose from the `kafka/` directory:

```bash
cd kafka
docker compose up -d
docker compose ps
```

The TimescaleDB service is built locally from `database/Dockerfile`. That
Dockerfile copies `database/init.sql` into the image so database initialization
does not depend on a host bind mount. This works consistently with Docker
Desktop on macOS and Windows and avoids host file-sharing permission errors.

The first startup may build the TimescaleDB image before the services start.

Useful local endpoints:

- Kafka: `localhost:9092`
- Kafka UI: [http://localhost:8080](http://localhost:8080)
- TimescaleDB: `localhost:5432`

### 2. Activate the Python Environment

Run the remaining commands from the repository root:

```bash
source .venv-1/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install -r producers/requirements.txt
pip install -r streams_app/requirements.txt
pip install psycopg2-binary
```

### 4. Create the Kafka Topic

The video producer and database consumer use the `traffic-events` topic:

```bash
docker exec kafka-local \
   /opt/kafka/bin/kafka-topics.sh \
   --create \
   --if-not-exists \
   --topic traffic-events \
   --bootstrap-server localhost:9092 \
   --partitions 1 \
   --replication-factor 1
```

Verify the topic:

```bash
docker exec kafka-local \
   /opt/kafka/bin/kafka-topics.sh \
   --list \
   --bootstrap-server localhost:9092
```

### 5. Confirm Video, GPS, and Model Files

The current video runner expects these files:

```bash
ls -lh data/raw/city/traffic_1.mp4
ls -lh data/raw/gps/traffic_1.gpx
ls -lh models/license-plate-finetune-v1s.pt
```

### 6. Start the Database Consumer

Open a separate terminal and run:

```bash
source .venv-1/bin/activate
python consumers/traffic_consumer.py
```

Expected output:

```text
Connected to TimescaleDB
Listening to Kafka topic: traffic-events
```

Keep this terminal running.

### 7. Process the MP4 Video

Open another terminal and run:

```bash
source .venv-1/bin/activate
python -m producers.run_traffic_video
```

Generated files:

```text
outputs/videos/traffic_1_output.mp4
data/processed/traffic_1/events.jsonl
data/processed/traffic_1/summary.json
```

### 8. Verify Database Records

Run these commands from any terminal:

```bash
docker exec timescaledb-local \
   psql \
   -U traffic_user \
   -d traffic_db \
   -c "SELECT COUNT(*) FROM traffic_events;"
```

View recent events:

```bash
docker exec timescaledb-local \
   psql \
   -U traffic_user \
   -d traffic_db \
   -c "SELECT event_time, event_type, track_id, vehicle_type FROM traffic_events ORDER BY event_time DESC LIMIT 10;"
```

### 9. Inspect Data in pgAdmin 4

Create a PostgreSQL server connection in pgAdmin 4 with these settings:

```text
Host: localhost
Port: 5432
Database: traffic_db
Username: traffic_user
Password: traffic_password
SSL mode: Disable
```

Open **Tools -> Query Tool** for the `traffic_db` database and run the following queries.

Check available tables:

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public';
```

<img src="DB_Screenshots/Screenshot%202026-09-12%20at%2010.45.41%E2%80%AFAM.png" alt="Available tables query result" width="700"/>

Count stored events:

```sql
SELECT COUNT(*) AS total_events
FROM traffic_events;
```
<img src="DB_Screenshots/Screenshot%202026-09-12%20at%2011.11.34%E2%80%AFAM.png" alt="Available tables - 11.11.34 AM" width="700"/>


View recent events:

```sql
SELECT
   event_time,
   event_type,
   track_id,
   vehicle_type,
   confidence,
   license_plate
FROM traffic_events
ORDER BY event_time DESC
LIMIT 20;
```
<img src="DB_Screenshots/Screenshot%202026-09-12%20at%2011.12.18%E2%80%AFAM.png" alt="Available tables - 11.12.18 AM" width="700"/>

Group events by type:

```sql
SELECT
   event_type,
   COUNT(*) AS event_count
FROM traffic_events
GROUP BY event_type
ORDER BY event_count DESC;
```
<img src="DB_Screenshots/Screenshot%202026-09-12%20at%2011.12.53%E2%80%AFAM.png" alt="Available tables - 11.12.53 AM" width="700"/>

Group vehicles by type:

```sql
SELECT
   vehicle_type,
   COUNT(*) AS vehicle_count
FROM traffic_events
GROUP BY vehicle_type
ORDER BY vehicle_count DESC;
```
<img src="DB_Screenshots/Screenshot%202026-09-12%20at%2011.13.21%E2%80%AFAM.png" alt="Available tables - 11.13.21 AM" width="700"/>


View events per minute:

```sql
SELECT
   date_trunc('minute', event_time) AS minute,
   COUNT(*) AS event_count
FROM traffic_events
GROUP BY minute
ORDER BY minute DESC;
```
<img src="DB_Screenshots/Screenshot%202026-09-12%20at%2011.14.09%E2%80%AFAM.png" alt="Available tables - 11.14.09 AM" width="700"/>

Count events from the last hour:

```sql
SELECT COUNT(*) AS events_last_hour
FROM traffic_events
WHERE event_time >= NOW() - INTERVAL '1 hour';
```

Inspect the complete raw event payload:

```sql
SELECT
   event_time,
   event_type,
   raw_event
FROM traffic_events
ORDER BY event_time DESC
LIMIT 10;
```

Check TimescaleDB hypertables:

```sql
SELECT *
FROM timescaledb_information.hypertables;
```
<img src="DB_Screenshots/Screenshot%202026-09-12%20at%2011.15.39%E2%80%AFAM.png" alt="Available tables - 11.15.39 AM" width="700"/>

## Windows Application Testing

The following commands assume **PowerShell**, Docker Desktop, and Git are installed.
Run the commands from the repository root unless a `cd kafka` command is shown.

### 1. Install System Prerequisites

Install FFmpeg and Git LFS using either `winget` or Chocolatey.

Using `winget`:

```powershell
winget install Gyan.FFmpeg.Shared
winget install GitHub.GitLFS
```

Or using Chocolatey:

```powershell
choco install ffmpeg git-lfs -y
```

Restart PowerShell, then verify the tools:

```powershell
ffprobe -version
git lfs version
git lfs install
```

Download the license-plate model weights:

```powershell
git lfs pull --include="models/*.pt"
```

### 2. Start Kafka and TimescaleDB

```powershell
Set-Location kafka
docker compose up -d
docker compose ps
Set-Location ..
```

Useful local endpoints:

- Kafka: `localhost:9092`
- Kafka UI: [http://localhost:8080](http://localhost:8080)
- TimescaleDB: `localhost:5432`

### 3. Create and Activate the Python Environment

Create the environment if it does not already exist:

```powershell
py -3.13 -m venv .venv-1
```

Activate it:

```powershell
.\.venv-1\Scripts\Activate.ps1
```

If PowerShell blocks script activation, run PowerShell as your user and retry:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### 4. Install Python Dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r producers\requirements.txt
python -m pip install -r streams_app\requirements.txt
python -m pip install psycopg2-binary
```

### 5. Create the Kafka Topic

```powershell
docker exec kafka-local /opt/kafka/bin/kafka-topics.sh --create --if-not-exists --topic traffic-events --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
```

Verify it:

```powershell
docker exec kafka-local /opt/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092
```

The output should include `traffic-events`.

### 6. Confirm Input Files

```powershell
Get-Item data\raw\city\traffic_1.mp4
Get-Item data\raw\gps\traffic_1.gpx
Get-Item models\license-plate-finetune-v1s.pt
```

### 7. Start the Database Consumer

Open a second PowerShell window in the repository root:

```powershell
.\.venv-1\Scripts\Activate.ps1
python consumers\traffic_consumer.py
```

Expected output:

```text
Connected to TimescaleDB
Listening to Kafka topic: traffic-events
```

Keep this window running.

### 8. Process the MP4 Video

Open a third PowerShell window in the repository root:

```powershell
.\.venv-1\Scripts\Activate.ps1
python -m producers.run_traffic_video
```

Generated files:

```text
outputs\videos\traffic_1_output.mp4
data\processed\traffic_1\events.jsonl
data\processed\traffic_1\summary.json
```

### 9. Verify TimescaleDB Records

```powershell
docker exec timescaledb-local psql -U traffic_user -d traffic_db -c "SELECT COUNT(*) FROM traffic_events;"
```

View recent events:

```powershell
docker exec timescaledb-local psql -U traffic_user -d traffic_db -c "SELECT event_time, event_type, track_id, vehicle_type FROM traffic_events ORDER BY event_time DESC LIMIT 10;"
```

---

## 🎯 Shared Group Commit Protocol & Roles
*   **Branch Isolation Rules:** Do not push updates directly to `main` or `master`. Always perform atomic checkouts (`git checkout -b feature/your-task`) and open an explicit Pull Request for evaluation.
*   **Storage Boundaries:** Because your `.gitignore` explicitly filters out `*.pt`, `*.onnx`, and binary text `*.mp4` assets, model data will remain safely outside GitHub system thresholds.

### Project Folders Ownership Matrix
*   **Teammates 1 & 2 (Computer Vision):** Manage `producers/` configurations to run live YOLO classification routines inside `mock_producer.py`.
*   **Teammates 3 & 4 (Analytics Framework):** Code windowed stream aggregation scripts in `streams_app/processors.py` and `aggregators.py`.
*   **Teammate 5 (Storage Core):** Maintain `consumers/traffic_consumer.py` and connect stored TimescaleDB data to dashboard platforms.
