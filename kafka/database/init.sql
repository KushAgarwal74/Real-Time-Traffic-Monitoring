CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS traffic_events (

    id BIGSERIAL,

    event_time TIMESTAMPTZ NOT NULL,

    event_type TEXT NOT NULL,

    track_id INTEGER NOT NULL,

    vehicle_type TEXT,

    confidence DOUBLE PRECISION,

    bbox JSONB,

    camera_gps JSONB,

    license_plate TEXT,

    plate_confidence DOUBLE PRECISION,

    raw_event JSONB NOT NULL,

    PRIMARY KEY (
        id,
        event_time
    )
);


SELECT create_hypertable(
    'traffic_events',
    'event_time',
    if_not_exists => TRUE
);


CREATE INDEX IF NOT EXISTS idx_traffic_events_track_id
ON traffic_events(track_id);


CREATE INDEX IF NOT EXISTS idx_traffic_events_event_type
ON traffic_events(event_type);