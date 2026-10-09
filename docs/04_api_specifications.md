# BHU-NETRA: Satellite Ground Segment & Mission Control Platform
## Document 04: API Specifications Catalog

---

### 1. API Architecture & Security Guidelines
BHU-NETRA exposes APIs across three protocol tiers:
1. **REST APIs (HTTP/2 - OpenAPI 3.0)**: Used for asynchronous management, mission planning, ordering, catalog metadata, and administrative operations.
2. **gRPC APIs (HTTP/2 - mTLS Protocol Buffers)**: Used for ultra-low-latency internal microservice communication, ground station control commands, and HSM cryptographic sign-offs.
3. **WebSocket / Server-Sent Events (SSE)**: Used for real-time telemetry streaming to Mission Control Consoles.

*Security*: All external and intra-cluster REST endpoints require OAuth2 Bearer Tokens (JWT) issued by Keycloak, carrying ABAC attributes (`user_department`, `clearance_level`, `spatial_scope`). Internal gRPC channels use Mutual TLS (mTLS) with SPIFFE/SPIRE identity attestation.

---

### 2. Core REST & gRPC API Endpoints Catalog

#### 2.1 Mission Planning & Orbit Scheduling API

##### `POST /api/v1/planning/passes/schedule`
* **Description**: Triggers optimization engine to compute ground station pass schedule and imaging plans.
* **Headers**: `Authorization: Bearer <JWT>`, `Content-Type: application/json`
* **Request Payload**:
```json
{
  "planning_window_start": "2026-10-10T00:00:00Z",
  "planning_window_end": "2026-10-11T00:00:00Z",
  "satellites": ["NETRA-EO-01", "NETRA-EO-02", "NETRA-SAR-01"],
  "ground_stations": ["GS-SHADNAGAR-01", "GS-PORTBLAIR-02", "GS-SVALBARD-01"],
  "include_weather_forecast": true
}
```
* **Response `(200 OK)`**:
```json
{
  "schedule_id": "SCH-20261010-0941",
  "status": "GENERATED",
  "total_passes": 14,
  "conflicts_resolved": 2,
  "passes": [
    {
      "pass_id": "PASS-NETRA01-SHAD-8842",
      "satellite_id": "NETRA-EO-01",
      "ground_station_id": "GS-SHADNAGAR-01",
      "aos_time": "2026-10-10T04:15:30Z",
      "los_time": "2026-10-10T04:27:12Z",
      "max_elevation_deg": 68.4,
      "task_type": "PAYLOAD_DOWNLINK_AND_TELEMETRY"
    }
  ]
}
```

##### `POST /api/v1/planning/tasking/emergency`
* **Description**: Preempts current pass schedule with top-priority emergency tasking request (e.g. Cyclone disaster response).
* **Request Payload**:
```json
{
  "requestor": "NDRF_DISASTER_OPS",
  "priority_level": "CRITICAL_OVERRIDE",
  "event_type": "CYCLONE_LANDFALL",
  "target_aoi": {
    "type": "Polygon",
    "coordinates": [[[85.2, 19.8], [86.5, 19.8], [86.5, 20.9], [85.2, 20.9], [85.2, 19.8]]]
  },
  "required_before": "2026-10-10T06:00:00Z"
}
```
* **Response `(202 Accepted)`**: Returns recalculated schedule preempting lower-priority optical imaging.

---

#### 2.2 Telemetry & Ground Station Handover API

##### `GET /api/v1/telemetry/satellites/{satellite_id}/realtime` (WebSocket)
* **Protocol**: `wss://c2.bhu-netra.gov.in/api/v1/telemetry/satellites/NETRA-EO-01/realtime`
* **Stream Message Output**:
```json
{
  "timestamp": "2026-10-09T18:10:00.125Z",
  "satellite_id": "NETRA-EO-01",
  "sequence_num": 10482,
  "telemetry": {
    "battery_soc_pct": 94.2,
    "bus_voltage_v": 28.1,
    "thermal_solar_array_c": 42.5,
    "thermal_payload_bay_c": 18.2,
    "aocs_quaternion": [0.012, 0.998, 0.004, 0.051],
    "reaction_wheel_rpm": [1200, 1180, 1205, -50],
    "fuel_pressure_bar": 14.8
  },
  "status_flag": "NOMINAL"
}
```

##### `POST /api/v1/handover/initiate` (gRPC / REST)
* **Description**: Initiates seamless mid-pass handover from Setting GS to Rising GS.
* **Request Payload**:
```json
{
  "satellite_id": "NETRA-EO-01",
  "source_gs_id": "GS-SHADNAGAR-01",
  "target_gs_id": "GS-PORTBLAIR-02",
  "handover_start_time": "2026-10-10T04:25:00Z",
  "carrier_frequency_hz": 2245000000,
  "sync_token": "TOK-HANDOVER-8842"
}
```
* **Response `(200 OK)`**:
```json
{
  "handover_status": "PHASE_LOCKED_AND_MIGRATED",
  "active_c2_ground_station": "GS-PORTBLAIR-02",
  "telemetry_loss_duration_ms": 0
}
```

---

#### 2.3 Cryptographic Command Authorization API (Air-Gapped Enclave)

##### `POST /api/v1/commands/authorizations/initiate`
* **Description**: Stage 1 Operator initiates telecommand request for satellite configuration or orbit maneuver.
* **Request Payload**:
```json
{
  "satellite_id": "NETRA-EO-01",
  "command_opcode": "CMD_AOCS_ORBIT_RAISE_EXECUTE",
  "parameters": {
    "delta_v_m_s": 0.45,
    "thruster_duration_sec": 12.5,
    "execution_time": "2026-10-10T05:00:00Z"
  },
  "operator_id": "OP-77412"
}
```
* **Response `(201 Created)`**: Returns `command_authorization_id: "CMD-AUTH-9914"` with `status: "PENDING_FDO_APPROVAL"`.

##### `POST /api/v1/commands/authorizations/{cmd_id}/sign`
* **Description**: Stages 2 & 3 sign-offs (Flight Dynamics Officer & Mission Director) utilizing Hardware Security Module (HSM) PKCS#11 signatures.
* **Request Payload**:
```json
{
  "command_authorization_id": "CMD-AUTH-9914",
  "approver_role": "MISSION_DIRECTOR",
  "approver_id": "MD-001",
  "hsm_token_signature": "MEQCID3k2x9...3d9a====",
  "approval_decision": "APPROVED"
}
```
* **Response `(200 OK)`**:
```json
{
  "command_authorization_id": "CMD-AUTH-9914",
  "status": "FULLY_AUTHORIZED_FOR_UPLINK",
  "ccsds_telecommand_hex": "1ACFFC1D0005774120011245...BCH_CRC_OK",
  "uplink_window": {
    "valid_from": "2026-10-10T04:55:00Z",
    "valid_until": "2026-10-10T05:05:00Z"
  }
}
```

---

#### 2.4 Data Catalog & Dissemination API (STAC Compliant)

##### `POST /api/v1/catalog/products/search`
* **Description**: OGC STAC SpatioTemporal Asset Search endpoint.
* **Request Payload**:
```json
{
  "bbox": [77.0, 8.0, 88.0, 22.0],
  "datetime": "2026-10-01T00:00:00Z/2026-10-09T23:59:59Z",
  "collections": ["NETRA-EO-01-L2-COG"],
  "query": {
    "eo:cloud_cover": { "lt": 15 }
  },
  "limit": 10
}
```
* **Response `(200 OK)`**:
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "id": "NETRA_EO01_20261008_SHAD_L2_0012",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[80.1, 16.2], [81.5, 16.2], [81.5, 17.5], [80.1, 17.5], [80.1, 16.2]]]
      },
      "properties": {
        "datetime": "2026-10-08T06:30:00Z",
        "satellite": "NETRA-EO-01",
        "gs_ingest": "GS-SHADNAGAR-01",
        "eo:cloud_cover": 4.2,
        "classification": "CONFIDENTIAL_GOV"
      },
      "assets": {
        "visual": {
          "href": "https://data.bhu-netra.gov.in/cog/2026/10/08/NETRA_EO01_L2.tif",
          "type": "image/tiff; application=geotiff; profile=cloud-optimized"
        }
      }
    }
  ]
}
```
