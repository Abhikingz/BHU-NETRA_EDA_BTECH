# BHU-NETRA: Satellite Ground Segment & Mission Control Platform
## Document 01: Comprehensive Functional & Non-Functional Specifications

---

### 1. Executive Summary & Mission Overview
**BHU-NETRA** is an enterprise-grade, national-scale satellite ground-segment and mission control platform (designed on the architectural principles of ISRO's ISTRAC and SAC systems). The system is architected to manage Telemetry, Tracking, and Command (TT&C) operations and payload data handling for a constellation of **40+ Earth Observation (EO) and Communication Satellites**.

The system handles:
1. **Continuous Orbit Tracking & Mid-Pass Handover** across domestic and international ground stations.
2. **Real-time Telemetry Ingestion & Automated Anomaly Detection** for critical satellite health parameters.
3. **Cryptographically Air-Gapped Multi-Sign-Off Command Authorization** workflow.
4. **High-Throughput Payload Ingestion & Automated Orthorectification** processing tens of terabytes daily.
5. **Dynamic Data Classification & Attribute-Based Access Control (ABAC)** for government vs. commercial subscribers.
6. **Constraint-Based Mission Planning & Pass Scheduling** with emergency priority overrides (e.g., disaster response).

---

### 2. Core Functional Requirements Breakdown

#### 2.1 Telemetry, Tracking, and Command (TT&C) & Ground Station Operations
* **Multi-Station Orbit Tracking & Steering**: Real-time antenna steering (Azimuth/Elevation) calculated via Two-Line Element (TLE) / SGP4/SDP4 propagation engines.
* **Seamless Mid-Pass Handover**: Handover control from a setting ground station (e.g., Shadnagar, Telangana) to a rising station (e.g., Port Blair, Andaman & Nicobar Islands or Svalbard, Norway) without dropping link state or command lock.
* **Doppler Shift & Frequency Tuning**: Real-time closed-loop tuning of transmitter/receiver frequencies for S-Band, X-Band, and Ka-Band hardware based on relative radial velocity.
* **Software-Defined Radio (SDR) & Legacy Interface Support**: Native capability to interface with older VITA 49 / analog baseband hardware (CPCI controllers, RS-422/serial) and modern SDR platforms (GNU Radio, USRP X410, Kratos Quantum).

#### 2.2 Satellite Health Telemetry & Anomaly Detection
* **Real-time Frame Demuxing**: Processing CCSDS 131.0-B-3 / 132.0-B-2 CADU (Channel Access Data Unit) frames at high ingestion rates.
* **Engineering Unit Calibration**: De-multiplexing raw bitstreams into physical units:
  * *Thermal*: Battery/Solar Array temperature (°C).
  * *Electrical*: Bus Voltage (V), Current Draw (A), Battery State of Charge (SoC %).
  * *Attitude & Orbit Control System (AOCS)*: Reaction wheel RPM, star tracker alignment, quaternions, sun sensors.
  * *Propulsion*: Hydrazine fuel tank pressure (Bar), thruster duty cycles.
* **Automated Anomaly Detection & Alerts**: Multi-tier alert thresholds (Yellow/Warning, Red/Critical) evaluated within <50ms. Automated escalation via PagerDuty, SMS, and Mission Control Console alarms.

#### 2.3 Cryptographic Multi-Sign-Off Command Authorization Workflow
* **Air-Gapped Command Security Enclave**: Hardware Security Module (HSM) protected command assembly.
* **3-Stage Authorization Matrix**:
  1. *Stage 1: Satellite Systems Engineer (Operator)* - Drafts telecommand package.
  2. *Stage 2: Flight Dynamics Officer (FDO)* - Validates trajectory, orbital safety window, and power impact.
  3. *Stage 3: Mission Director (MD)* - Final cryptographic sign-off using Hardware Token / PKI.
* **Telecommand Generation**: Framing according to CCSDS Telecommand 231.0-B-3 with BCH error correction and sequence counters to prevent replay attacks.

#### 2.4 Payload Ingestion, Processing & Geo-Referencing
* **High-Throughput Downlink Ingestion**: Receiving multi-spectral, panchromatic, Synthetic Aperture Radar (SAR), and hyperspectral data downlinked at 1.2 Gbps to 10 Gbps per ground station pass.
* **Automated Level-0 to Level-3 Processing Pipeline**:
  * *Level-0*: Raw demuxed payload frames with checksum verification.
  * *Level-1*: Radiometric calibration and sensor nonlinearity correction.
  * *Level-2*: Geometric correction, DEM orthorectification, and geo-referencing (GeoTIFF / COG format).
  * *Level-3*: Mosaic generation, cloud mask filtering, and change detection indexing.
* **Storage Tiering**: Immediate ingest to NVMe Hot Tier, staging to Warm SAN (5 PB), and long-term archiving to Cold LTO Tape / Object Storage.

#### 2.5 Mission Planning & Pass Scheduling Engine
* **Constrained Optimization Scheduler**: Evaluates orbital pass geometry, ground station availability, power budgets, sensor thermal limits, and onboard storage capacity.
* **Weather & Cloud Cover Integration**: Automated ingest of IMD (India Meteorological Department) and ECMWF weather forecasts to prioritize cloud-free imaging passes.
* **Emergency Override Protocol**: Priority queues for national emergency events (e.g., cyclone, flood monitoring by NDRF), auto-preempting routine optical imaging passes within 15 minutes of trigger.

#### 2.6 Data Classification, Entitlements & Dissemination
* **Security Classification Engine**:
  * *Restricted / Defense*: High-resolution imagery of strategic areas; stored strictly on-prem, encrypted with GOV-Grade HSM keys.
  * *Government Ministries (Agri, Disaster, Forestry)*: Full resolution imagery delivered via secure, direct G2G network links (NICNET).
  * *Commercial / Academic*: Open / Paid tier with dynamic spatial downsampling, cloud-masking, or geographic boundary redaction.
* **Cloud-Hosted Dissemination Portal**: Public/subscriber web portal supporting OGC standards (WMS, WMTS, WFS, STAC API) hosted on accredited public cloud, completely isolated from Core C2 networks via unidirectional Data Diodes.

---

### 3. Non-Functional Requirements (NFRs)

| NFR Category | Metric / Requirement | Architectural Mechanism |
| :--- | :--- | :--- |
| **Availability** | 99.999% (Five Nines) for TT&C functions | Multi-region active-active GS controllers, VRRP failover |
| **Latency** | <50ms telemetry alert processing; <5s command transmission lock | In-memory time-series processing (TimescaleDB / Redis) |
| **Throughput** | 50+ Terabytes/day payload ingestion across 40 satellites | Distributed parallel processing with Ray/Apache Spark & NVMe arrays |
| **Security** | Air-gapped Command Enclave, FIPS 140-3 Level 3 HSM | Unidirectional Data Diodes, PKI Multi-sign-off |
| **Interoperability** | CCSDS 131.0, 132.0, 231.0, VITA 49, OGC STAC | Abstracted GS Adapter Interface Layer |
| **Compliance** | CERT-In Security Guidelines, ISRO Mission Standards | Immutable Append-Only Kafka Audit Ledger |

---

### 4. System Boundaries & Air-Gap Architecture

```
+-----------------------------------------------------------------------------------+
|                            SECURE ON-PREMISE INFRASTRUCTURE                        |
|                                                                                   |
|  +------------------------+      +------------------------+      +-----------------+  |
|  |  Legacy / SDR Ground   | <--> |  Core Mission Control  | <--> |  Command HSM    |  |
|  |  Stations (TT&C/X-Band)|      |  Telemetry & C2 Engine |      |  Security Enclave|  |
|  +------------------------+      +------------------------+      +-----------------+  |
|                                              |                                    |
|                                              v                                    |
|                                  +------------------------+                       |
|                                  | Level-0 to Level-3 HPC |                       |
|                                  | Geo-Processing Engine  |                       |
|                                  +------------------------+                       |
+----------------------------------------------|------------------------------------+
                                               | (Unidirectional Data Diode)
                                               v
+-----------------------------------------------------------------------------------+
|                        DMZ / CLOUD DISSEMINATION PORTAL                           |
|                                                                                   |
|  +------------------------+      +------------------------+      +-----------------+  |
|  | OGC STAC Catalog API   | <--> | Attribute Access Control| <--> | Public & G2G    |  |
|  | & GeoServer Cluster    |      | (Keycloak / ABAC Engine)|      | Subscriber Web  |  |
|  +------------------------+      +------------------------+      +-----------------+  |
+-----------------------------------------------------------------------------------+
```
