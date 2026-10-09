-- BHU-NETRA PostgreSQL + PostGIS Core Database Schema
-- Version 1.0.0
-- Target Engine: PostgreSQL 16+ with PostGIS 3.4+

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Satellites Catalog
CREATE TABLE IF NOT EXISTS satellites (
    satellite_id VARCHAR(32) PRIMARY KEY,
    norad_id INTEGER UNIQUE NOT NULL,
    name VARCHAR(64) NOT NULL,
    constellation VARCHAR(64) NOT NULL,
    orbit_type VARCHAR(16) NOT NULL CHECK (orbit_type IN ('LEO', 'MEO', 'GEO', 'SSO')),
    inclination_deg NUMERIC(5,2) NOT NULL,
    altitude_km NUMERIC(6,2) NOT NULL,
    operational_status VARCHAR(16) DEFAULT 'ACTIVE' CHECK (operational_status IN ('ACTIVE', 'MAINTENANCE', 'DECOMMISSIONED')),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 2. Ground Stations Network
CREATE TABLE IF NOT EXISTS ground_stations (
    ground_station_id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(64) NOT NULL,
    location_geom GEOMETRY(Point, 4326) NOT NULL,
    altitude_meters NUMERIC(7,2) NOT NULL,
    country VARCHAR(32) NOT NULL,
    supported_bands TEXT[] NOT NULL, -- e.g. ARRAY['S-BAND', 'X-BAND', 'KA-BAND']
    is_sdr_capable BOOLEAN DEFAULT TRUE,
    status VARCHAR(16) DEFAULT 'ONLINE' CHECK (status IN ('ONLINE', 'OFFLINE', 'DEGRADED')),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 3. Pass Schedules & Geometry
CREATE TABLE IF NOT EXISTS pass_schedules (
    pass_id VARCHAR(64) PRIMARY KEY,
    satellite_id VARCHAR(32) NOT NULL REFERENCES satellites(satellite_id),
    ground_station_id VARCHAR(32) NOT NULL REFERENCES ground_stations(ground_station_id),
    aos_time TIMESTAMPTZ NOT NULL,
    los_time TIMESTAMPTZ NOT NULL,
    max_elevation_deg NUMERIC(4,1) NOT NULL CHECK (max_elevation_deg >= 0 AND max_elevation_deg <= 90),
    operation_mode VARCHAR(32) NOT NULL,
    schedule_status VARCHAR(24) DEFAULT 'PLANNED' CHECK (schedule_status IN ('PLANNED', 'EXECUTING', 'COMPLETED', 'PREEMPTED', 'CANCELLED')),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_pass_time CHECK (los_time > aos_time)
);

-- 4. Multi-Sign-Off Command Authorization Ledger
CREATE TABLE IF NOT EXISTS command_authorizations (
    command_authorization_id VARCHAR(64) PRIMARY KEY,
    satellite_id VARCHAR(32) NOT NULL REFERENCES satellites(satellite_id),
    pass_id VARCHAR(64) REFERENCES pass_schedules(pass_id),
    opcode VARCHAR(64) NOT NULL,
    parameters JSONB NOT NULL,
    operator_id VARCHAR(32) NOT NULL,
    fdo_id VARCHAR(32),
    md_id VARCHAR(32),
    hsm_key_id VARCHAR(64),
    cryptographic_signature TEXT,
    approval_status VARCHAR(32) DEFAULT 'PENDING_OPERATOR' CHECK (approval_status IN ('PENDING_OPERATOR', 'PENDING_FDO', 'PENDING_MD', 'FULLY_AUTHORIZED', 'REJECTED', 'EXECUTED')),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 5. Payload Imagery Catalog (STAC Item Table)
CREATE TABLE IF NOT EXISTS payload_products (
    product_id VARCHAR(64) PRIMARY KEY,
    pass_id VARCHAR(64) NOT NULL REFERENCES pass_schedules(pass_id),
    satellite_id VARCHAR(32) NOT NULL REFERENCES satellites(satellite_id),
    ground_station_id VARCHAR(32) NOT NULL REFERENCES ground_stations(ground_station_id),
    processing_level VARCHAR(8) NOT NULL CHECK (processing_level IN ('L0', 'L1', 'L2', 'L3')),
    footprint_geom GEOMETRY(Polygon, 4326) NOT NULL,
    acquisition_time TIMESTAMPTZ NOT NULL,
    cloud_cover_pct NUMERIC(4,2) CHECK (cloud_cover_pct >= 0 AND cloud_cover_pct <= 100),
    classification VARCHAR(32) NOT NULL CHECK (classification IN ('RESTRICTED', 'CONFIDENTIAL_GOV', 'PUBLIC_LICENSED')),
    storage_s3_uri TEXT NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    checksum_sha256 VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 6. Audit Ledger Table (Append-Only)
CREATE TABLE IF NOT EXISTS system_audit_logs (
    audit_id BIGSERIAL PRIMARY KEY,
    event_type VARCHAR(64) NOT NULL,
    actor_id VARCHAR(64) NOT NULL,
    target_resource VARCHAR(128) NOT NULL,
    action_details JSONB NOT NULL,
    ip_address INET,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Spatial Indexes
CREATE INDEX IF NOT EXISTS idx_gs_location ON ground_stations USING GIST(location_geom);
CREATE INDEX IF NOT EXISTS idx_products_footprint ON payload_products USING GIST(footprint_geom);
CREATE INDEX IF NOT EXISTS idx_products_acq_time ON payload_products(acquisition_time);
CREATE INDEX IF NOT EXISTS idx_pass_time ON pass_schedules(aos_time, los_time);
