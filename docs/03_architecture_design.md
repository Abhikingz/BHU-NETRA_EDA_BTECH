# BHU-NETRA: Satellite Ground Segment & Mission Control Platform
## Document 03: Dual Architecture Design – Open Source vs. Enterprise Proprietary

---

### 1. Introduction & Comparative Philosophy
To satisfy national strategic autonomy, sovereign security, and technology evaluation guidelines, two complete end-to-end architectures have been designed for **BHU-NETRA**:

1. **Architecture Stack A: Indigenous & Open-Source First Stack**
   * *Philosophy*: Built on proven open-source frameworks, open standards (OGC, CCSDS, VITA 49), indigenous libraries, and open-source geospatial tools. Eliminates vendor lock-in, allows full source-code auditability, and provides complete strategic autonomy for air-gapped defense and government installations.
2. **Architecture Stack B: Non-Open Source / Enterprise Proprietary Stack**
   * *Philosophy*: Built on turn-key commercial enterprise suites (Ansys STK, Oracle, IBM MQ, ESRI ArcGIS, Kratos Quantum). Offers commercial SLAs, out-of-the-box regulatory compliance, and off-the-shelf support contracts at higher licensing costs.

---

### 2. Side-by-Side Architectural Layer Comparison

| Architectural Layer | Architecture Stack A (Indigenous / Open-Source) | Architecture Stack B (Enterprise / Proprietary) |
| :--- | :--- | :--- |
| **Operating System** | Rocky Linux 9 / Red Hat Enterprise Linux (Community Build) / Ubuntu 22.04 LTS (Kernel hardened) | Red Hat Enterprise Linux (RHEL Enterprise Server with Red Hat Satellite) |
| **Orbital Dynamics & Propagation** | **Orekit (Java)** + **GDT (Ground Segment Development Toolkit)** + Python SGP4 | **Ansys STK (Satellite Tool Kit) Systems Tool Kit Engine** + Orbit Determination Tool Kit (ODTK) |
| **Baseband & SDR Processing** | **GNU Radio 3.10** + **VITA 49 (Libvita49)** + USRP UHD API | **Kratos Quantum Radio** / **AWS Ground Station API** / RT Logic Telemetry Processors |
| **Message Broker & Stream Ingest** | **Apache Kafka** (Core Event Stream) + **Apache Pulsar** / **EMQX** (Telemetry MQTT) | **IBM MQ Enterprise** + **Solace PubSub+ Event Broker** |
| **Relational & Spatial Database** | **PostgreSQL 16** + **PostGIS 3.4** | **Oracle Database 19c Enterprise Edition** + **Oracle Spatial and Graph** |
| **Time-Series Telemetry DB** | **TimescaleDB** (PostgreSQL Extension) / Apache Druid | **InfluxDB Enterprise** / AVEVA PI System (OSIsoft PI) |
| **Object Storage (Payload)** | **MinIO Enterprise** (S3 Compliant, Multi-Node Erasure Coding) / Ceph | **NetApp StorageGRID** / Dell EMC Elastic Cloud Storage (ECS) |
| **Geospatial Processing Engine** | **GDAL / OGR** + **Orfeo ToolBox (OTB)** + **PDAL** + Python Rasterio | **ESRI ArcGIS Enterprise Server** + **ERDAS IMAGINE Engine** |
| **Map Rendering & OGC Services** | **GeoServer 2.24** + **OpenLayers 8 / Deck.gl** | **ESRI ArcGIS Image Server** + ArcGIS Portal Map Viewer |
| **Orchestration & Workflow** | **Apache Airflow 2.8** + **Kubernetes / K3s (Air-gapped cluster)** | **VMware Tanzu Application Platform** / Red Hat OpenShift Container Platform |
| **Identity & Access Control** | **Keycloak 23** (OpenID Connect / OAuth2 / SAML2) + FreeIPA (LDAP) | **Ping Identity Enterprise** + Microsoft Active Directory / CyberArk |
| **Hardware Security Module (HSM)**| **Thales Luna HSM (PKCS#11 Open API)** / SoftHSM2 (Dev) | **Thales PayShield / SafeNet Network HSM Enterprise Suite** |
| **Audit & Logging** | **OpenSearch 2.11 / Vector** | **Splunk Enterprise** + IBM QRadar |

---

### 3. Detailed Architecture Stack A: Indigenous & Open-Source First Stack

#### 3.1 Core Architecture Diagram (Open-Source Stack)

```
+---------------------------------------------------------------------------------------------------------+
|                                    AIR-GAPPED ON-PREMISE MISSION CONTROL                                 |
|                                                                                                         |
|  +-----------------------+     +------------------------+     +--------------------------------------+  |
|  | Legacy GS / SDR Node  |     | Message & Stream Layer |     | Command Security Enclave (Air-Gapped)|  |
|  | (GNU Radio / VITA 49) | --> | Apache Kafka / Pulsar  | <-> | Keycloak + SoftHSM2/Thales PKCS#11   |  |
|  +-----------------------+     +------------------------+     +--------------------------------------+  |
|              |                             |                                     |                      |
|              v                             v                                     v                      |
|  +-----------------------+     +------------------------+     +--------------------------------------+  |
|  | Telemetry Ingest      |     | Mission Planning & Orbit|     | PostGIS + TimescaleDB                |  |
|  | (CCSDS Decoder / C++) |     | Propagation (Orekit)   |     | Telemetry & Metadata Storage         |  |
|  +-----------------------+     +------------------------+     +--------------------------------------+  |
|              |                             |                                     |                      |
|              +-----------------------------+-------------------------------------+                      |
|                                            |                                                            |
|                                            v                                                            |
|                                +------------------------+                                               |
|                                | Level-0 to Level-3     |                                               |
|                                | Geo-Processing Cluster |                                               |
|                                | (GDAL / OTB / Airflow) |                                               |
|                                +------------------------+                                               |
+--------------------------------------------|------------------------------------------------------------+
                                             | (Unidirectional Hardware Data Diode)
                                             v
+---------------------------------------------------------------------------------------------------------+
|                                   DMZ / CLOUD DISSEMINATION PORTAL                                      |
|                                                                                                         |
|  +-------------------------------+    +-------------------------------+    +--------------------------+ |
|  | MinIO S3 Object Storage       |    | GeoServer / STAC Catalog      |    | Subscriber Web Portal    | |
|  | (Public / Gov COG Images)     | -> | (OGC WMS / WMTS / STAC API)   | -> | (OpenLayers / Deck.gl)   | |
|  +-------------------------------+    +-------------------------------+    +--------------------------+ |
+---------------------------------------------------------------------------------------------------------+
```

#### 3.2 Strengths of Open-Source Architecture Stack A
1. **Complete Sovereignty & Security Auditability**: Full access to source code ensures zero backdoors and adherence to strict defense air-gap policies.
2. **Zero Recurring License Fees**: Scalable to 100+ satellites and 20+ ground stations without per-core or per-satellite licensing costs.
3. **High Adaptability**: Customized DSP algorithms can be added directly into GNU Radio or Orekit.

---

### 4. Detailed Architecture Stack B: Enterprise Proprietary Stack

#### 4.1 Core Architecture Diagram (Proprietary Stack)

```
+---------------------------------------------------------------------------------------------------------+
|                                    AIR-GAPPED ON-PREMISE MISSION CONTROL                                 |
|                                                                                                         |
|  +-----------------------+     +------------------------+     +--------------------------------------+  |
|  | Kratos Quantum Baseband|    | Solace PubSub+ /       |     | CyberArk + Thales PayShield HSM      |  |
|  | Hardware Processors   | --> | IBM MQ Enterprise      | <-> | Air-Gapped Command Gateway           |  |
|  +-----------------------+     +------------------------+     +--------------------------------------+  |
|              |                             |                                     |                      |
|              v                             v                                     v                      |
|  +-----------------------+     +------------------------+     +--------------------------------------+  |
|  | InfluxDB Enterprise   |     | Ansys STK Engine &     |     | Oracle Database 19c Enterprise       |  |
|  | Telemetry Store       |     | Orbit Determination    |     | + Oracle Spatial and Graph           |  |
|  +-----------------------+     +------------------------+     +--------------------------------------+  |
|              |                             |                                     |                      |
|              +-----------------------------+-------------------------------------+                      |
|                                            |                                                            |
|                                            v                                                            |
|                                +------------------------+                                               |
|                                | ESRI ArcGIS Server     |                                               |
|                                | & ERDAS IMAGINE HPC    |                                               |
|                                +------------------------+                                               |
+--------------------------------------------|------------------------------------------------------------+
                                             | (Unidirectional Hardware Data Diode)
                                             v
+---------------------------------------------------------------------------------------------------------+
|                                   DMZ / CLOUD DISSEMINATION PORTAL                                      |
|                                                                                                         |
|  +-------------------------------+    +-------------------------------+    +--------------------------+ |
|  | NetApp StorageGRID            |    | ESRI ArcGIS Portal &          |    | ArcGIS Web AppBuilder    | |
|  | Enterprise Object Storage     | -> | Image Server Cluster          | -> | Commercial Subscriber UI | |
|  +-------------------------------+    +-------------------------------+    +--------------------------+ |
+---------------------------------------------------------------------------------------------------------+
```

#### 4.2 Strengths of Proprietary Architecture Stack B
1. **Commercial Vendor SLAs**: Turn-key support from Ansys, Oracle, ESRI, and IBM with guaranteed incident response times.
2. **Pre-Certified Compliance**: Out-of-the-box compliance with international space standards and enterprise IT frameworks.
3. **Turn-Key GUIs**: Rich GUI applications for STK flight dynamics officers and ArcGIS GIS analysts.

---

### 5. Architectural Evaluation Matrix

| Evaluation Criteria | Stack A (Open-Source / Indigenous) | Stack B (Enterprise Proprietary) | Recommended Winner |
| :--- | :--- | :--- | :--- |
| **Strategic Autonomy** | **10 / 10** (Full control over code & algorithms) | 3 / 10 (Subject to export controls / sanctions) | **Stack A** |
| **Air-Gap Feasibility** | **10 / 10** (Zero phone-home / offline license keys) | 5 / 10 (Requires license server management) | **Stack A** |
| **Total Cost of Ownership (TCO)**| **Low Capital Expenditure** (Engineering cost only) | High ($5M+ annual license renewal) | **Stack A** |
| **Speed of Initial Deployment**| Medium (Requires system integration) | **High** (Off-the-shelf software modules) | Stack B |
| **Performance at Scale** | **High** (Distributed Kafka/MinIO/PostGIS scales linearly)| High (Requires high hardware allocation) | **Tie** |

**Conclusion**: For **BHU-NETRA**, **Architecture Stack A (Open-Source & Indigenous First)** is the recommended primary deployment for core Mission Control (TT&C and C2), ensuring national sovereignty and immunity from external trade/vendor restrictions.
