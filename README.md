# BHU-NETRA: Satellite Ground Segment & Mission Control Platform
### Enterprise System Architecture, Specifications & Reference Implementation
**Case 6 Assignment Solution | Group 6 (Team Size: 7)**

---

## Executive Summary
**BHU-NETRA** is an enterprise-grade, sovereign satellite ground-segment and mission control platform (designed on the architectural principles of ISRO's ISTRAC and SAC systems). It is engineered for Telemetry, Tracking, and Command (TT&C) operations of a growing constellation of **40+ Earth Observation (EO) and Communication satellites**, and for high-throughput ingestion, processing, and dissemination of multi-terabyte payload imagery to government departments and research subscribers.

---

## 📁 Repository Structure & Artifacts Catalog

| Directory / File | Description | Assignment Requirement |
| :--- | :--- | :--- |
| [`docs/01_functionality_spec.md`](docs/01_functionality_spec.md) | Comprehensive Functional & Non-Functional Specifications (TT&C, Handover, Security, Telemetry) | **(a) Functionality List** |
| [`docs/02_microservices_architecture.md`](docs/02_microservices_architecture.md) | Microservices Catalog, Bounded Contexts & Inter-service Communication Protocols | **(b) Micro-services** |
| [`docs/03_architecture_design.md`](docs/03_architecture_design.md) | **Dual Architecture Design**: Open Source / Indigenous Stack vs. Enterprise Proprietary Stack | **(c) Architecture Design** |
| [`docs/04_api_specifications.md`](docs/04_api_specifications.md) | REST, gRPC, and WebSocket API Documentation with Request/Response payloads | **(d) API Details** |
| [`api/openapi_spec.yaml`](api/openapi_spec.yaml) | Complete **OpenAPI 3.0 YAML** specification | **(d) API Details** |
| [`docs/05_hardware_specifications.md`](docs/05_hardware_specifications.md) | Ground Station RF Antennas, SDRs, HPC GPU Cluster, Storage Tiers, and Security Enclave | **(e) Hardware Details** |
| [`docs/06_data_flow_map.md`](docs/06_data_flow_map.md) | **8-Stage Satellite Pass Journey Data Flow Map**, Schemas, and Persistence Architecture | **(f) Data Flow Map & DB** |
| [`schemas/`](schemas/) | Formal JSON & XML XSD Schemas for all 8 pass stages | **(f) Data Schemas** |
| [`database/`](database/) | PostgreSQL/PostGIS DDL (`init_postgres_postgis.sql`), TimescaleDB SQL, and MinIO storage policies | **(f) Persistence Design** |
| [`services/`](services/) | Runnable microservices (Mission Planner, Command Enclave, SDR Gateway, Dissemination Portal) | **Runnable Implementation** |
| [`scripts/test_all_services.py`](scripts/test_all_services.py) | **End-to-End Simulation Test Suite** executing the complete satellite pass journey | **E2E Simulation Runner** |
| [`scripts/init_git_repo.py`](scripts/init_git_repo.py) | Git repository setup & GitHub push helper script | **GitHub Push Tooling** |
| [`docker-compose.yml`](docker-compose.yml) | Docker sandbox setup for PostGIS, Redis, MinIO, and microservices | **Container Deployment** |

---

## 🚀 Quick Start: Running the End-to-End Simulation

The repository includes a zero-dependency Python simulation test runner that launches all microservices and simulates a complete 8-stage Satellite Pass Journey in real time.

```bash
# 1. Navigate to the project folder
cd bhu-netra

# 2. Run the End-to-End Satellite Pass Journey simulation
python scripts/test_all_services.py
```

### Expected Output Screenshot / Log:
```text
================================================================================
      BHU-NETRA: SATELLITE PASS JOURNEY END-TO-END SIMULATION SUITE
================================================================================

[STAGE 1] Querying Mission Planner for Satellite Pass Schedule...
 -> Schedule Generated: SCH-20261009-78C5 (Total Passes: 3)
 -> Pass ID: PASS-NETRA-E-SHAD-FBF1 | Sat: NETRA-EO-01 | GS: GS-SHADNAGAR-01

[STAGE 2 & 3] Ingesting Real-Time Telemetry Stream & Anomaly Check...
 -> Event ID: TEL-EVT-B8029C67 | CADU Frame: #97998
 -> Bus Voltage: 27.81V | Battery SoC: 93.4%
 -> Anomaly Status: NOMINAL

[STAGE 4] Executing 3-Stage Air-Gapped Command Authorization Workflow...
 -> Stage 1 (Operator): Command Created -> ID: CMD-AUTH-BC666E [Status: PENDING_FDO_APPROVAL]
 -> Stage 2 (FDO): Approved Orbit & Power Window [Status: PENDING_MD_APPROVAL]
 -> Stage 3 (Mission Director HSM): Cryptographic Signature Generated!
 -> CCSDS Telecommand Frame: 1ACFFC1D000577412001124584C814C652D1E4A5BCH_CRC_OK
 -> Final State: FULLY_AUTHORIZED_FOR_UPLINK (Ready for Uplink)

[STAGE 5] Executing Mid-Pass Ground Station Control Handover...
 -> Handover ID: HO-20261009-6993
 -> Transfer: GS-SHADNAGAR-01 -> GS-PORTBLAIR-02
 -> Link State: PHASE_LOCK_SYNCHRONIZED_SUCCESS | Telemetry Continuity: ZERO_FRAME_LOSS

[STAGE 6 - 8] Searching STAC Imagery Catalog & Ordering Data Dissemination...
 -> STAC Items Found: 2
 -> Selected STAC Item: NETRA_EO01_20261010_L3_AGRI_COG_091 (L3 COG)
 -> Delivery Envelope ID: DEL-20261009-AAE6
 -> Recipient: MINISTRY_OF_AGRICULTURE via NICNET_DIRECT_GOV_BACKBONE
 -> ABAC Policy Applied: Classification Mask = True
 -> Storage URI: s3://bhu-netra-level3-products/2026/10/10/NETRA_EO01_20261010_L3_AGRI_COG_091.tif

================================================================================
 SUCCESS: ALL 8 STAGES OF SATELLITE PASS JOURNEY SIMULATED SUCCESSFULLY!
================================================================================
```

---

## 🌐 Pushing Code to GitHub

To push this complete repository to your remote GitHub account:

```bash
# Run the git push script with your GitHub repository URL:
python scripts/init_git_repo.py https://github.com/YOUR_USERNAME/BHU-NETRA.git [YOUR_GITHUB_TOKEN]
```

---

## 🏛️ Architectural Comparison Summary

| Metric | Open-Source Stack (Stack A) | Proprietary Stack (Stack B) |
| :--- | :--- | :--- |
| **Orbit Dynamics** | Orekit (Java) + GDT | Ansys STK Engine |
| **Database** | PostgreSQL 16 + PostGIS 3.4 | Oracle 19c Enterprise + Spatial |
| **Telemetry Ingest**| TimescaleDB + Apache Kafka | InfluxDB + Solace PubSub+ |
| **Geo-Processing** | GDAL / Orfeo ToolBox + MinIO | ESRI ArcGIS Enterprise + NetApp StorageGRID |
| **Sovereignty** | **100% Air-Gap Sovereign (No External Licensing)** | Subject to export controls & recurring vendor fees |
