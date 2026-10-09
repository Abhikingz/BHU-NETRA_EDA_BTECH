-- TimescaleDB Satellite Telemetry Hypertable Setup
-- Version 1.0.0

CREATE TABLE IF NOT EXISTS satellite_telemetry (
    time TIMESTAMPTZ NOT NULL,
    satellite_id VARCHAR(32) NOT NULL,
    pass_id VARCHAR(64),
    ground_station_id VARCHAR(32),
    bus_voltage_v NUMERIC(5,2),
    solar_array_current_a NUMERIC(5,2),
    battery_soc_pct NUMERIC(4,1),
    payload_temp_c NUMERIC(4,1),
    battery_pack_temp_c NUMERIC(4,1),
    reaction_wheel_rpm_q1 INTEGER,
    reaction_wheel_rpm_q2 INTEGER,
    reaction_wheel_rpm_q3 INTEGER,
    reaction_wheel_rpm_q4 INTEGER,
    fuel_pressure_bar NUMERIC(5,2),
    has_anomaly BOOLEAN DEFAULT FALSE,
    severity VARCHAR(16) DEFAULT 'NOMINAL'
);

-- Convert to hypertable partitioned by time (7-day chunk interval)
SELECT create_hypertable('satellite_telemetry', 'time', chunk_time_interval => INTERVAL '7 days', if_not_exists => TRUE);

-- Create compound index for ultra-fast time-series satellite telemetry queries
CREATE INDEX IF NOT EXISTS idx_sat_telemetry_time ON satellite_telemetry (satellite_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_telemetry_anomaly ON satellite_telemetry (satellite_id, time DESC) WHERE has_anomaly = TRUE;
