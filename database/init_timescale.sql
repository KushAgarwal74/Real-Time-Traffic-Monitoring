CREATE EXTENSION IF NOT EXISTS timescaledb;

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

SELECT create_hypertable('traffic_event', 'event_time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_traffic_event_camera_time
ON traffic_event (camera_location, event_time DESC);

CREATE INDEX IF NOT EXISTS idx_traffic_event_time
ON traffic_event (event_time DESC);
