# BHU-NETRA: Satellite Ground Segment & Mission Control Platform
## Document 06: Satellite Pass Journey – Data Flow Map, Schemas & Persistence Design

---

### 1. End-to-End Satellite Pass Journey Data Flow Map

The complete lifecycle of a single satellite pass journey spans 8 distinct operational stages from long-range orbit planning down to government payload delivery:

```
[ STAGE 1: Mission Planning & Orbit Schedule ] 
       | (Generates Pass Schedule XML/JSON)
       v
[ STAGE 2: Ground Station Antenna Tracking & AOS Acquisition ]
       | (SDR Lock & Baseband Ingest)
       v
[ STAGE 3: Telemetry Stream Ingestion & Real-Time Alert Evaluation ]
       | (Parses CCSDS Frames -> TimescaleDB)
       v
[ STAGE 4: Multi-Sign-Off Cryptographic Command Authorization ]
       | (Operator -> FDO -> MD HSM Approval -> Uplink)
       v
[ STAGE 5: Mid-Pass Ground Station Control Handover ]
       | (Shadnagar GS -> Port Blair GS Handover)
       v
[ STAGE 6: Payload Downlink Ingestion & Raw Staging ]
       | (X/Ka Band 10Gbps Ingest -> NVMe Hot Tier)
       v
[ STAGE 7: Level-1 to Level-3 Geo-Processing & Calibration ]
       | (Radiometric + Orthorectification -> COG in MinIO)
       v
[ STAGE 8: Entitlement Check & Data Dissemination Delivery ]
       | (ABAC Verification -> NICNET Delivery to Ministry of Agriculture)
```

---

### 2. Concrete Data Schemas & Payload Formats per Stage

#### STAGE 1: Mission Planning Pass Schedule (XML Schema & JSON)

##### XML Pass Schedule Payload (`pass_schedule.xml`)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<SatellitePassSchedule xmlns="http://bhu-netra.gov.in/schemas/planning/v1"
                       scheduleId="SCH-20261010-0941"
                       generatedAt="2026-10-09T18:00:00Z">
    <PlanningWindow start="2026-10-10T00:00:00Z" end="2026-10-11T00:00:00Z"/>
    <PassDetails passId="PASS-NETRA01-SHAD-8842">
        <Satellite id="NETRA-EO-01" noradId="58912"/>
        <GroundStation id="GS-SHADNAGAR-01" lat="17.0315" lon="78.1842" altMeters="540.0"/>
        <PassGeometry aos="2026-10-10T04:15:30Z" los="2026-10-10T04:27:12Z" maxElevationDeg="68.4"/>
        <OperationMode>PAYLOAD_DOWNLINK_AND_TELEMETRY</OperationMode>
        <TargetArea name="ANDHRA_PRADESH_AGRICULTURE_ZONE">
            <BoundingBox minLon="79.5" minLat="15.0" maxLon="81.2" maxLat="17.0"/>
        </TargetArea>
    </PassDetails>
</SatellitePassSchedule>
```

---

#### STAGE 3: Telemetry Event Payload (JSON Stream)

##### Live Telemetry Parameter Frame (`telemetry_event.json`)
```json
{
  "event_id": "TEL-EVT-99824102",
  "timestamp": "2026-10-10T04:16:02.450Z",
  "satellite_id": "NETRA-EO-01",
  "pass_id": "PASS-NETRA01-SHAD-8842",
  "ground_station_id": "GS-SHADNAGAR-01",
  "raw_cadu_sequence": 10482,
  "parameters": {
    "electrical": {
      "bus_voltage_v": 28.14,
      "solar_array_current_a": 18.5,
      "battery_soc_pct": 96.8
    },
    "thermal": {
      "payload_camera_temp_c": 16.4,
      "battery_pack_temp_c": 21.0,
      "hydrazine_tank_temp_c": 24.2
    },
    "aocs": {
      "quaternion": [0.0125, 0.9981, 0.0042, 0.0511],
      "reaction_wheel_rpm": [1200, 1185, 1202, 0],
      "earth_pointing_error_deg": 0.008
    },
    "propulsion": {
      "fuel_tank_pressure_bar": 14.82
    }
  },
  "anomaly_status": {
    "has_anomaly": false,
    "severity": "NOMINAL"
  }
}
```

---

#### STAGE 4: Multi-Sign-Off Command Authorization Payload (JSON)

##### Cryptographically Signed Command (`command_authorization.json`)
```json
{
  "command_authorization_id": "CMD-AUTH-9914",
  "satellite_id": "NETRA-EO-01",
  "target_pass_id": "PASS-NETRA01-SHAD-8842",
  "telecommand": {
    "opcode": "CMD_PAYLOAD_CAMERA_POWER_ON",
    "parameters": {
      "sensor_mode": "MULTI_SPECTRAL_HIGH_RES",
      "duration_seconds": 240
    }
  },
  "sign_off_chain": [
    {
      "stage": 1,
      "role": "SYSTEM_OPERATOR",
      "user_id": "OP-77412",
      "timestamp": "2026-10-10T03:30:00Z",
      "status": "APPROVED"
    },
    {
      "stage": 2,
      "role": "FLIGHT_DYNAMICS_OFFICER",
      "user_id": "FDO-3004",
      "timestamp": "2026-10-10T03:45:00Z",
      "status": "APPROVED"
    },
    {
      "stage": 3,
      "role": "MISSION_DIRECTOR",
      "user_id": "MD-001",
      "timestamp": "2026-10-10T04:00:00Z",
      "status": "APPROVED",
      "hsm_key_id": "THALES-LUNA-KEY-C2-PROD-01",
      "cryptographic_signature": "MEQCID3k2x9YvB6aN...831a9=="
    }
  ],
  "ccsds_framed_hex": "1ACFFC1D0005774120011245...BCH_CRC_OK",
  "uplink_execution_status": "READY_FOR_UPLINK"
}
```

---

#### STAGE 5: Mid-Pass Ground Station Control Handover Payload (JSON)

##### Mid-Pass Handover Event (`handover_protocol.json`)
```json
{
  "handover_id": "HO-20261010-0012",
  "satellite_id": "NETRA-EO-01",
  "timestamp": "2026-10-10T04:22:00.000Z",
  "receding_ground_station": {
    "gs_id": "GS-SHADNAGAR-01",
    "current_elevation_deg": 8.2,
    "rf_link_status": "RELEASE_CARRIER_LOCK"
  },
  "approaching_ground_station": {
    "gs_id": "GS-PORTBLAIR-02",
    "current_elevation_deg": 12.5,
    "rf_link_status": "ACQUIRED_CARRIER_LOCK"
  },
  "handover_phase": "PHASE_LOCK_SYNCHRONIZED",
  "telemetry_stream_continuity": "ZERO_FRAME_LOSS"
}
```

---

#### STAGE 8: Processed Payload GeoTIFF Product Metadata & Delivery (JSON)

##### Dissemination Delivery Envelope (`dissemination_entitlement.json`)
```json
{
  "delivery_id": "DEL-20261010-GOV-AGRI-004",
  "recipient_department": "MINISTRY_OF_AGRICULTURE",
  "recipient_network": "NICNET_DIRECT_GOV_BACKBONE",
  "clearance_level": "CONFIDENTIAL_GOV",
  "product": {
    "product_id": "NETRA_EO01_20261010_L3_AGRI_COG_091",
    "stac_item_url": "https://data.bhu-netra.gov.in/api/v1/catalog/items/NETRA_EO01_20261010_L3_AGRI_COG_091",
    "spatial_resolution_meters": 0.5,
    "format": "Cloud-Optimized GeoTIFF (COG)",
    "storage_uri": "s3://bhu-netra-level3-products/2026/10/10/NETRA_EO01_20261010_L3_AGRI.tif",
    "checksum_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  },
  "entitlement_policy": {
    "spatial_watermark_applied": false,
    "classification_mask_applied": true,
    "redacted_sensitive_zones": ["STRATEGIC_DEFENSE_ZONE_4"]
  },
  "delivered_at": "2026-10-10T05:15:00Z"
}
```

---

### 3. Comprehensive Database Design & Persistence Architecture

#### 3.1 PostgreSQL + PostGIS Relational Schema DDL (`init_postgres_postgis.sql`)

```sql
-- BHU-NETRA Core Relational & Geospatial Schema
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Satellites Master Table
CREATE TABLE satellites (
    satellite_id VARCHAR(32) PRIMARY KEY,
    norad_id INTEGER UNIQUE NOT NULL,
    name VARCHAR(64) NOT NULL,
    constellation VARCHAR(64) NOT NULL,
    orbit_type VARCHAR(16) NOT NULL, -- LEO, GEO, MEO
    inclination_deg NUMERIC(5,2) NOT NULL,
    operational_status VARCHAR(16) DEFAULT 'ACTIVE'
);

-- 2. Ground Stations Master Table
CREATE TABLE ground_stations (
    ground_station_id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(64) NOT NULL,
    location_geom GEOMETRY(Point, 4326) NOT NULL,
    altitude_meters NUMERIC(7,2) NOT NULL,
    supported_bands VARCHAR(64)[] NOT NULL, -- {'S-BAND', 'X-BAND', 'KA-BAND'}
    is_sdr_capable BOOLEAN DEFAULT TRUE,
    status VARCHAR(16) DEFAULT 'ONLINE'
);

-- 3. Satellite Pass Schedule Table
CREATE TABLE pass_schedules (
    pass_id VARCHAR(64) PRIMARY KEY,
    satellite_id VARCHAR(32) REFERENCES satellites(satellite_id),
    ground_station_id VARCHAR(32) REFERENCES ground_stations(ground_station_id),
    aos_time TIMESTAMPTZ NOT NULL,
    los_time TIMESTAMPTZ NOT NULL,
    max_elevation_deg NUMERIC(4,1) NOT NULL,
    operation_mode VARCHAR(32) NOT NULL,
    schedule_status VARCHAR(24) DEFAULT 'PLANNED',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 4. Level-0 to Level-3 Payload Products Metadata (STAC Catalog Table)
CREATE TABLE payload_products (
    product_id VARCHAR(64) PRIMARY KEY,
    pass_id VARCHAR(64) REFERENCES pass_schedules(pass_id),
    satellite_id VARCHAR(32) REFERENCES satellites(satellite_id),
    processing_level VARCHAR(8) NOT NULL, -- L0, L1, L2, L3
    footprint_geom GEOMETRY(Polygon, 4326) NOT NULL,
    acquisition_time TIMESTAMPTZ NOT NULL,
    cloud_cover_pct NUMERIC(4,2),
    classification VARCHAR(32) NOT NULL, -- RESTRICTED, CONFIDENTIAL_GOV, PUBLIC
    storage_s3_uri TEXT NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    checksum_sha256 VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Spatial Indexes
CREATE INDEX idx_gs_location ON ground_stations USING GIST(location_geom);
CREATE INDEX idx_products_footprint ON payload_products USING GIST(footprint_geom);
CREATE INDEX idx_products_acq_time ON payload_products(acquisition_time);
```

#### 3.2 TimescaleDB Telemetry Hypertable DDL (`telemetry_timescale.sql`)

```sql
-- TimescaleDB Telemetry Time-Series Hypertable
CREATE TABLE satellite_telemetry (
    time TIMESTAMPTZ NOT NULL,
    satellite_id VARCHAR(32) NOT NULL,
    bus_voltage_v NUMERIC(5,2),
    solar_array_current_a NUMERIC(5,2),
    battery_soc_pct NUMERIC(4,1),
    payload_temp_c NUMERIC(4,1),
    reaction_wheel_rpm INTEGER[],
    fuel_pressure_bar NUMERIC(5,2),
    anomaly_flag BOOLEAN DEFAULT FALSE
);

-- Convert to Hypertable partitioned by time
SELECT create_hypertable('satellite_telemetry', 'time');
CREATE INDEX idx_sat_telemetry_time ON satellite_telemetry (satellite_id, time DESC);
```

#### 3.3 Redis Live Caching & Session Key Structure
* `live:telemetry:<satellite_id>` -> Hash containing latest telemetry frame (<10ms lookup).
* `live:pass:active:<gs_id>` -> Active pass geometry & lock status.
* `live:handover:state:<satellite_id>` -> Handover state machine lock.

#### 3.4 MinIO S3 Object Storage Bucket Topology
* `bhu-netra-raw-level0/` -> Raw `.dat` CADU bitstream demux files.
* `bhu-netra-calibrated-level1/` -> Radiometrically corrected TIFFs.
* `bhu-netra-level2-cog/` -> Orthorectified Cloud-Optimized GeoTIFFs (Warm Tier).
* `bhu-netra-level3-mosaic/` -> Multi-date mosaic COGs & disaster change maps.
