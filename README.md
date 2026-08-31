# Real-Time Traffic Monitoring System (YOLO + Apache Kafka)

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

## 🚀 Local setup and end-to-end run

### 1. Prerequisites
Make sure you have:
- Docker Desktop or Docker Engine running locally
- Python 3.11+ (this project was validated with Python 3.13)
- Access to the project root folder

### 2. Start the infrastructure services
From the project root:
```bash
docker compose up -d
```

This starts:
- Kafka at `localhost:9092`
- ZooKeeper at `localhost:2181`
- Kafka UI at `http://localhost:8080`
- TimescaleDB at `localhost:5432`

### 3. Create and activate a Python virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install the project dependencies
```bash
pip install --upgrade pip
pip install -r producers/requirements.txt
pip install -r streams_app/requirements.txt
```

If you are working directly with the DB and Kafka config, also install the runtime dependencies used by the app environment, including the Kafka client and psycopg packages:
```bash
pip install confluent-kafka "psycopg[binary]>=3.3.4"
```

### 5. Configure local environment values
Copy the example environment file and keep the values aligned with the local Docker stack:
```bash
cp .env.example .env
```

The current `.env.example` includes:
```env
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_RAW_TOPIC=traffic-raw-data
KAFKA_CONSUMER_GROUP=traffic-monitoring-analytics-group

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=traffic_db
POSTGRES_USER=traffic_user
POSTGRES_PASSWORD=traffic_password

DATABASE_URL=postgresql://traffic_user:traffic_password@localhost:5432/traffic_db
```

### 6. Verify database connectivity
Use the TimescaleDB container to confirm the database is accepting connections:
```bash
docker exec -it timescaledb-local psql -U traffic_user -d traffic_db -c "SELECT current_database(), current_user;"
```

You should see the database and user names returned successfully.

To inspect the database tables:
```bash
docker exec -it timescaledb-local psql -U traffic_user -d traffic_db -c "\dt"
```

The expected tables include:
- `traffic_event`
- `traffic_summary`

### 7. Run the app end to end
Start the consumer in one terminal:
```bash
source .venv/bin/activate
./.venv/bin/python consumers/dashboard_sink.py
```

This consumer will:
- ensure the Kafka topic exists
- initialize the database schema if needed
- wait for raw traffic events from Kafka
- insert them into `traffic_event`
- update the minute summary table

In a second terminal, run the producer:
```bash
source .venv/bin/activate
./.venv/bin/python producers/mock_producer.py
```

The producer sends mock camera data into the `traffic-raw-data` Kafka topic. The DB sink consumes that stream and writes the results into TimescaleDB.

### 8. Verify the pipeline is working
Check the consumer terminal for output like:
```text
[DB Sink] saved frame 1 from intersection_north_highway | total=15 | breakdown={'car': 8, 'truck': 2, 'bus': 1, 'motorcycle': 4}
```

Check the database directly:
```bash
docker exec -it timescaledb-local psql -U traffic_user -d traffic_db -c "SELECT count(*) FROM traffic_event;"
```

You can also inspect the summary table:
```bash
docker exec -it timescaledb-local psql -U traffic_user -d traffic_db -c "SELECT * FROM traffic_summary ORDER BY bucket_start DESC LIMIT 10;"
```

### 9. Stop the pipeline cleanly
```bash
Ctrl+C
```
If needed, stop the infrastructure stack:
```bash
docker compose down
```

---

## 🎯 Project flow summary
The project is designed as:

1. Producer emits traffic detections to Kafka
2. Kafka broker handles the event stream
3. Consumer writes raw frames to TimescaleDB
4. Summary logic aggregates traffic by minute and classifies congestion
5. Dashboard or alerting queries can consume the summary data

This is the verified local pattern used in the current repo setup.
