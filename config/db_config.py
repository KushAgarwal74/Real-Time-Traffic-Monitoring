import json
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import psycopg

from config.settings import DATABASE_URL


def floor_to_minute(ts: datetime) -> datetime:
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.replace(second=0, microsecond=0)


def classify_congestion(vehicle_count: int) -> str:
    if vehicle_count < 10:
        return "low"
    if vehicle_count < 25:
        return "medium"
    return "high"


@contextmanager
def get_db_connection():
    conn = psycopg.connect(DATABASE_URL, connect_timeout=5)
    try:
        yield conn
    finally:
        conn.close()


def init_database():
    last_error = None
    for attempt in range(1, 11):
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS traffic_event (
                            event_id BIGSERIAL,
                            event_time TIMESTAMPTZ NOT NULL,
                            camera_location TEXT NOT NULL,
                            frame_id BIGINT NOT NULL,
                            total_vehicles INTEGER NOT NULL,
                            detection_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
                            raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                            PRIMARY KEY (event_id, event_time)
                        );
                        """
                    )
                    cur.execute(
                        """
                        SELECT create_hypertable('traffic_event', 'event_time', if_not_exists => TRUE);
                        """
                    )
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS traffic_summary (
                            camera_location TEXT NOT NULL,
                            bucket_start TIMESTAMPTZ NOT NULL,
                            total_vehicles INTEGER NOT NULL,
                            average_vehicles NUMERIC(10, 2) NOT NULL,
                            max_vehicles INTEGER NOT NULL,
                            congestion_level TEXT NOT NULL,
                            frame_count INTEGER NOT NULL,
                            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                            PRIMARY KEY (camera_location, bucket_start)
                        );
                        """
                    )
                    cur.execute(
                        """
                        SELECT create_hypertable('traffic_summary', 'bucket_start', if_not_exists => TRUE);
                        """
                    )
                    cur.execute(
                        """
                        CREATE INDEX IF NOT EXISTS idx_traffic_event_camera_time
                        ON traffic_event (camera_location, event_time DESC);
                        """
                    )
                    cur.execute(
                        """
                        CREATE INDEX IF NOT EXISTS idx_traffic_event_time
                        ON traffic_event (event_time DESC);
                        """
                    )
                    cur.execute(
                        """
                        CREATE INDEX IF NOT EXISTS idx_traffic_summary_camera_time
                        ON traffic_summary (camera_location, bucket_start DESC);
                        """
                    )
                conn.commit()
            return
        except Exception as exc:  # pragma: no cover - runtime startup safeguard
            last_error = exc
            time.sleep(2)

    raise RuntimeError(f"Database initialization failed after retries: {last_error}")


def ensure_traffic_summary_table():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS traffic_summary (
                    camera_location TEXT NOT NULL,
                    bucket_start TIMESTAMPTZ NOT NULL,
                    total_vehicles INTEGER NOT NULL,
                    average_vehicles NUMERIC(10, 2) NOT NULL,
                    max_vehicles INTEGER NOT NULL,
                    congestion_level TEXT NOT NULL,
                    frame_count INTEGER NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    PRIMARY KEY (camera_location, bucket_start)
                );
                """
            )
            cur.execute(
                """
                SELECT create_hypertable('traffic_summary', 'bucket_start', if_not_exists => TRUE);
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_traffic_summary_camera_time
                ON traffic_summary (camera_location, bucket_start DESC);
                """
            )
        conn.commit()


def upsert_traffic_summary(camera_location: str, bucket_start: datetime, total_vehicles: int, frame_count: int = 1):
    ensure_traffic_summary_table()
    bucket_start = floor_to_minute(bucket_start)
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT total_vehicles, frame_count, max_vehicles
                FROM traffic_summary
                WHERE camera_location = %s AND bucket_start = %s
                """,
                (camera_location, bucket_start),
            )
            row = cur.fetchone()

            if row is None:
                next_total = int(total_vehicles)
                next_frame_count = int(frame_count)
                next_max = int(total_vehicles)
            else:
                prev_total, prev_frames, prev_max = row
                next_total = int(prev_total) + int(total_vehicles)
                next_frame_count = int(prev_frames) + int(frame_count)
                next_max = max(int(prev_max), int(total_vehicles))

            average_vehicles = (next_total / next_frame_count) if next_frame_count else 0.0
            congestion_level = classify_congestion(int(round(average_vehicles)))

            cur.execute(
                """
                INSERT INTO traffic_summary (
                    camera_location,
                    bucket_start,
                    total_vehicles,
                    average_vehicles,
                    max_vehicles,
                    congestion_level,
                    frame_count,
                    updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (camera_location, bucket_start)
                DO UPDATE SET
                    total_vehicles = EXCLUDED.total_vehicles,
                    average_vehicles = EXCLUDED.average_vehicles,
                    max_vehicles = EXCLUDED.max_vehicles,
                    congestion_level = EXCLUDED.congestion_level,
                    frame_count = EXCLUDED.frame_count,
                    updated_at = NOW()
                """,
                (
                    camera_location,
                    bucket_start,
                    next_total,
                    average_vehicles,
                    next_max,
                    congestion_level,
                    next_frame_count,
                ),
            )
        conn.commit()


def get_hourly_summary(camera_location: str | None = None, hours: int = 1):
    ensure_traffic_summary_table()
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            sql = """
                SELECT
                    camera_location,
                    date_trunc('hour', bucket_start) AS hour_bucket,
                    SUM(total_vehicles) AS total_vehicles,
                    ROUND(AVG(average_vehicles), 2) AS average_vehicles,
                    MAX(max_vehicles) AS peak_vehicles
                FROM traffic_summary
                WHERE bucket_start >= NOW() - make_interval(hours => %s)
            """
            params = [hours]
            if camera_location:
                sql += " AND camera_location = %s "
                params.append(camera_location)
            sql += " GROUP BY camera_location, date_trunc('hour', bucket_start) ORDER BY hour_bucket DESC "
            cur.execute(sql, tuple(params))
            return cur.fetchall()


def insert_traffic_event(event_payload: dict):
    event_time_raw = event_payload.get("event_time")
    if isinstance(event_time_raw, datetime):
        event_time = event_time_raw
    elif isinstance(event_time_raw, str):
        try:
            event_time = datetime.fromisoformat(event_time_raw)
        except ValueError:
            event_time = datetime.now(timezone.utc)
    else:
        event_time = datetime.now(timezone.utc)

    camera_location = event_payload.get("camera_location", "unknown")
    total_vehicles = int(sum(int(v) for v in event_payload.get("detections", {}).values() if isinstance(v, (int, float))))

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO traffic_event (
                    event_time,
                    camera_location,
                    frame_id,
                    total_vehicles,
                    detection_summary,
                    raw_payload
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    event_time,
                    camera_location,
                    int(event_payload.get("frame_id", 0)),
                    total_vehicles,
                    json.dumps(event_payload.get("detections", {})),
                    json.dumps(event_payload),
                ),
            )
        conn.commit()
    upsert_traffic_summary(camera_location, event_time, total_vehicles)
