# BHU-NETRA: Satellite Ground Segment & Mission Control Platform
## Document 02: Microservices Architecture & Service Catalog

---

### 1. Architectural Overview & Domain Decomposition

BHU-NETRA is structured into **four core domain bounded contexts**:
1. **Orbital & Mission Planning Domain (OMPD)**: Pass scheduling, orbit propagation, emergency tasking.
2. **TT&C & Flight Operations Domain (TFOD)**: Baseband ingest, real-time telemetry, command enclave, GS handover.
3. **Payload & Geo-Processing Domain (PGPD)**: High-throughput ingestion, radiometric/geometric calibration, mosaic engine.
4. **Dissemination & Governance Domain (DGPD)**: STAC catalog, ABAC policy engine, public/government web portal.

```
                  +-------------------------------------------------+
                  |          BHU-NETRA MICROSERVICES MAP            |
                  +-------------------------------------------------+
                                           |
    +-------------------+------------------+------------------+-------------------+
    |                   |                                     |                   |
+---v---------------+ +-v-----------------+                 +-v-----------------+ +-v-----------------+
| ORBITAL & MISSION | | TT&C & FLIGHT     |                 | PAYLOAD & GEO     | | DISSEMINATION &   |
| PLANNING DOMAIN   | | OPERATIONS DOMAIN |                 | PROCESSING DOMAIN | | GOVERNANCE DOMAIN|
+-------------------+ +-------------------+                 +-------------------+ +-------------------+
| • orbit-propagator| | • gs-adapter-sdr  |                 | • payload-ingest  | | • catalog-stac    |
| • pass-scheduler  | | • telemetry-ingest|                 | • image-calib-l1  | | • abac-entitle    |
| • tasking-override| | • anomaly-alert   |                 | • geoprocess-l2-l3| | • portal-gateway  |
|                   | | • command-enclave |                 | • storage-tierer  | | • audit-compliance|
|                   | | • handover-ctrl   |                 |                   | |                   |
+-------------------+ +-------------------+                 +-------------------+ +-------------------+
```

---

### 2. Microservice Detailed Specifications

#### 2.1 Orbital & Mission Planning Domain

##### Service 1: `orbit-propagator-service`
* **Primary Responsibility**: Solves satellite orbital mechanics (SGP4/SDP4 propagation), calculates TLE updates, predicts ground station visibility passes, elevation/azimuth acquisition loss times (AOS/LOS), and Doppler shifts.
* **Tech Stack**: Python / Java (Orekit library), C++ core for high-speed calculation.
* **Protocols**: gRPC for internal real-time calculations; REST for batch queries.
* **Database**: PostgreSQL (Satellite ephemeris, TLE records).

##### Service 2: `pass-scheduler-service`
* **Primary Responsibility**: Constraint-satisfaction engine (OR-Tools / OptaPlanner) that generates multi-satellite, multi-ground-station operational schedules considering battery levels, memory buffers, and sensor availability.
* **Protocols**: REST API, Kafka event emitter (`pass.scheduled`).
* **Database**: PostgreSQL (Pass schedules, conflict logs).

##### Service 3: `tasking-override-service`
* **Primary Responsibility**: Manages priority request queue (e.g. NDRF disaster response). Automatically recalculates schedules and revokes lower-priority imaging commands.
* **Protocols**: REST / gRPC, Kafka (`tasking.emergency_preempt`).

---

#### 2.2 TT&C & Flight Operations Domain

##### Service 4: `gs-adapter-sdr-service`
* **Primary Responsibility**: Abstraction layer between physical Ground Station hardware and core software. Connects to legacy Baseband processors via VITA 49 / TCP streams and modern Software Defined Radios (GNU Radio / USRP X410).
* **Protocols**: VITA 49 (VITA Radio Transport over UDP), TCP sockets, C++ native bindings.
* **Database**: Redis (Live baseband link status, AGC levels, carrier lock state).

##### Service 5: `telemetry-ingestion-pipeline`
* **Primary Responsibility**: De-multiplexes CCSDS CADU/VCFrames, decodes Reed-Solomon / LDPC error correction, extracts telemetry parameters (Voltage, Thermal, AOCS), and calibrates raw counts to engineering units.
* **Protocols**: UDP stream, Apache Kafka ingestion (`telemetry.raw_frames`, `telemetry.calibrated`).
* **Database**: TimescaleDB (Time-series telemetry hypertable).

##### Service 6: `anomaly-alerting-service`
* **Primary Responsibility**: Real-time evaluation of telemetry parameter thresholds and ML anomaly models (Isolation Forest / LSTM autoencoders). Triggers instant mission alarms.
* **Protocols**: Kafka consumer, WebSocket stream to Mission Control Consoles, Webhooks (PagerDuty/SMS).
* **Database**: Redis (Active alarms cache), PostgreSQL (Historical anomaly events).

##### Service 7: `command-authorization-enclave`
* **Primary Responsibility**: Air-gapped, multi-sign-off state machine. Manages the 3-stage sign-off (Operator -> FDO -> Mission Director), integrates with FIPS 140-3 HSM for digital signatures, and generates encrypted CCSDS Telecommand frames.
* **Protocols**: gRPC (TLS 1.3 with mTLS & HSM PKCS#11 driver).
* **Database**: PostgreSQL (Immutable command authorization logs), Hardware Security Module (Private keys).

##### Service 8: `gs-handover-controller`
* **Primary Responsibility**: Coordinates real-time mid-pass handover between ground stations. Executes RF frequency lock transfer, telemetry stream sync, and command link migration.
* **Protocols**: gRPC, Kafka (`handover.initiated`, `handover.completed`).
* **Database**: Redis (Live handover state machine).

---

#### 2.3 Payload & Geo-Processing Domain

##### Service 9: `payload-downlink-ingester`
* **Primary Responsibility**: Parallel high-speed ingestion of X-Band and Ka-Band raw sensor payloads (up to 10 Gbps per pass). Performs CRC verification and writes to Hot NVMe arrays.
* **Protocols**: VITA 49 / High-speed TCP socket, gRPC.
* **Database**: MinIO / S3 Object Storage (Raw Level-0 `.dat` files).

##### Service 10: `image-calibration-l1-service`
* **Primary Responsibility**: Performs dark current subtraction, flat-field correction, gain adjustment, and detector radiometric calibration.
* **Protocols**: Distributed worker queue (Ray Cluster / Celery / Airflow).

##### Service 11: `geoprocess-l2-l3-service`
* **Primary Responsibility**: Executes geometric orthorectification, DEM alignment (using Cartosat/SRTM DEMs), cloud masking, pan-sharpening, and COG (Cloud-Optimized GeoTIFF) generation.
* **Protocols**: GDAL / Orfeo Toolbox / PDAL bindings over Python/C++.
* **Database**: MinIO / S3 (Level-2 and Level-3 GeoTIFF products).

##### Service 12: `storage-tierer-service`
* **Primary Responsibility**: Automated lifecycle management of payload artifacts across Hot NVMe (0-7 days), Warm SAN (8-90 days), and Cold LTO Tape / Deep Archive (>90 days).
* **Protocols**: REST API, Cron schedule.

---

#### 2.4 Dissemination & Governance Domain

##### Service 13: `catalog-stac-service`
* **Primary Responsibility**: Implements OGC SpatioTemporal Asset Catalog (STAC) API 1.0.0. Enables spatio-temporal spatial querying (BBOX, Point, Polygon, Date range, Sensor, Cloud cover %).
* **Protocols**: REST API (OpenAPI 3.0), GeoJSON.
* **Database**: PostgreSQL + PostGIS (Spatial indexing on `geometry` column).

##### Service 14: `abac-entitlement-service`
* **Primary Responsibility**: Attribute-Based Access Control (ABAC) engine. Evaluates user clearance (Gov Ministry vs Commercial Subscriber), spatial boundaries, classification policy, and spatial resolution limits before serving products.
* **Protocols**: gRPC / REST (Keycloak OAuth2 / OIDC JWT validation).
* **Database**: PostgreSQL (User policies, subscription contracts).

##### Service 15: `portal-gateway-service`
* **Primary Responsibility**: API Gateway providing public and G2G web portal backends. Integrates GeoServer for WMS/WMTS map tile rendering and image downloads.
* **Protocols**: REST, OGC WMS/WMTS/WFS.

##### Service 16: `audit-compliance-logger`
* **Primary Responsibility**: Centralized, tamper-evident audit ledger capturing every telecommand approval, ground station handover, telemetry anomaly, and imagery download.
* **Protocols**: Kafka event consumer, immutable append-only ledger.
* **Database**: PostgreSQL append-only tables / Elasticsearch.

---

### 3. Inter-Service Communication Matrix

| Source Service | Target Service | Interaction Pattern | Protocol / Payload | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `pass-scheduler-service` | `gs-adapter-sdr-service` | Asynchronous Event | Kafka (`pass.scheduled`) | Upload tracking schedule to GS antenna controller |
| `gs-adapter-sdr-service` | `telemetry-ingestion-pipeline` | Stream | UDP / VITA 49 Stream | Ingest raw telemetry byte stream |
| `telemetry-ingestion-pipeline` | `anomaly-alerting-service` | Event Stream | Kafka (`telemetry.calibrated`) | Evaluate thresholds in real-time |
| `command-authorization-enclave` | `gs-adapter-sdr-service` | Synchronous mTLS | gRPC | Send cryptographically signed command frame for uplink |
| `gs-handover-controller` | `gs-adapter-sdr-service` | Synchronous gRPC | gRPC | Switch command carrier lock between GS nodes |
| `payload-downlink-ingester` | `image-calibration-l1-service` | Task Queue | Celery / Ray Queue | Trigger Level-1 calibration on completed pass |
| `geoprocess-l2-l3-service` | `catalog-stac-service` | REST / Event | Kafka (`product.published`) | Register COG metadata in PostGIS STAC Catalog |
| `portal-gateway-service` | `abac-entitlement-service` | Synchronous gRPC | gRPC | Verify subscriber license & classification before delivery |
