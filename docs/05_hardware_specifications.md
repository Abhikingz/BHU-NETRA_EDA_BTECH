# BHU-NETRA: Satellite Ground Segment & Mission Control Platform
## Document 05: Hardware Specifications & Ground Infrastructure Engineering

---

### 1. Overview & Operational Environment
BHU-NETRA operates across a hybrid physical infrastructure encompassing:
1. **Primary Mission Operations Complex (MOX)**: Centralized, air-gapped tier-IV data center housing core C2, telemetry, and HPC geo-processing clusters.
2. **Domestic Ground Station Network**: Deep-space and EO ground stations (e.g., Shadnagar, Hyderabad; Hassan, Karnataka; Port Blair, A&N).
3. **International / Polar Ground Stations**: Svalbard, Norway; Antarctica (Bharati Station); and polar downlink facilities.
4. **Cloud Dissemination DMZ**: Hosted on government-accredited cloud infrastructure.

---

### 2. Ground Station RF, Antenna Pedestal & Baseband Hardware

```
+-----------------------------------------------------------------------------------+
|                        GROUND STATION HARDWARE STACK                              |
|                                                                                   |
|  [ 11m S/X/Ka Tri-Band Cassegrain Antenna ]                                        |
|                       |                                                           |
|       (Dual-Polarized Diplexer & Feed Horn)                                       |
|                       |                                                           |
|        +--------------+--------------+                                            |
|        | (Downlink)                  | (Uplink)                                   |
|        v                             v                                            |
|  [ Cooled LNA (Noise Temp <45K) ]  [ 500W SSPA / TWTA High-Power Amp ]               |
|        |                             ^                                            |
|        v                             |                                            |
|  [ Downconverter (X/Ka -> L-Band) ] [ Upconverter (L-Band -> S-Band) ]            |
|        |                             |                                            |
|        v                             |                                            |
|  +-----------------------------------+-----------------------------------------+  |
|  | Baseband Digitizer & SDR Frontend (USRP X410 / VITA 49 FEP Engine)          |  |
|  +-----------------------------------------------------------------------------+  |
|                                      |                                            |
|                 (10GbE Fiber Backhaul / VITA 49 UDP Packets)                      |
|                                      v                                            |
|                       [ Edge Compute Buffer Node ]                                |
+-----------------------------------------------------------------------------------+
```

#### 2.1 Antenna Systems & RF Frontends
* **Antenna Reflector**: 11-meter & 7.5-meter Cassegrain Tri-Band (S-Band, X-Band, Ka-Band) parabolic tracking dish with monopulse auto-tracking feed.
* **Tracking Servo Controller**: Antenna Control Unit (ACU) with dual-axis brushless AC servo motors providing 15 deg/sec azimuth and 10 deg/sec elevation slew rates.
* **Low Noise Amplifiers (LNA)**: Cryogenically/thermo-electrically cooled X-band LNA (Noise Temperature < 45 K; G/T ratio > 32 dB/K at 5 deg elevation).
* **High Power Amplifiers (HPA)**: Dual 500W Solid-State Power Amplifiers (SSPA) with automatic switchover for S-Band command uplink.

#### 2.2 Baseband & Software Defined Radio (SDR) Hardware
* **Digitizer / Front-End Processor (FEP)**: USRP X410 Quad-Channel SDR with Dual 100GbE interfaces and Xilinx Zynq UltraScale+ RFSoC.
* **VITA 49 Engine**: Hardware packetizer digitizing RF IF (Intermediate Frequency) signals directly into VITA 49 VRT streams over 10GbE optical links.
* **Legacy FEP Converter**: PCI-Express / CPCI telemetry demodulator cards handling legacy PCM/FM, BPSK, and QPSK modulation formats for older ground station assets.

---

### 3. On-Premise High-Performance Compute (HPC) & Server Infrastructure

#### 3.1 Mission Operations & C2 Core Cluster
* **Master Control Server Nodes (x6 HA Nodes)**:
  * *Processor*: Dual AMD EPYC 9654 (96 Cores, 192 Threads per CPU, 2.4 GHz base).
  * *RAM*: 1.5 TB ECC DDR5-4800 MHz.
  * *Network*: Dual-port 100GbE Mellanox ConnectX-6 SmartNICs with RoCEv2 support.
  * *OS*: Hardened Rocky Linux 9 (Air-gapped kernel with SELinux Enforcing).

#### 3.2 Real-time Geo-Processing GPU Cluster (Level-0 to Level-3 Ingest)
* **HPC Compute Nodes (x16 Nodes)**:
  * *Processor*: Dual Intel Xeon Platinum 8480+ (56 Cores per CPU).
  * *GPUs*: 4x NVIDIA H100 80GB SXM5 GPUs per node (Total 64 H100 GPUs across cluster) connected via NVLink for parallel orthorectification, SAR phase processing, and radiometric calibration.
  * *RAM*: 1 TB ECC DDR5.
  * *Storage*: Local 15.36 TB NVMe U.3 PCIe 5.0 Scratch Disk per node.

---

### 4. Multi-Tier Storage Subsystems Architecture

| Storage Tier | Technology Stack | Capacity | Read/Write Throughput | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 0 (Hot NVMe Array)** | Pure Storage FlashArray//XL or Custom Ceph NVMe Cluster | 200 Terabytes | 100 Gigabits/sec (Direct DMA) | Real-time pass ingestion, raw bitstream demuxing |
| **Tier 1 (Warm SAN/NAS)** | MinIO Enterprise / NetApp StorageGRID (100GbE Backhaul)| 5 Petabytes | 40 Gigabits/sec | 90-day active imagery COG store & PostGIS spatial catalog |
| **Tier 2 (Cold Tape Archive)** | IBM TS4500 LTO-9 Enterprise Tape Library (Dual Robotics) | 18 Petabytes (Expandable) | 400 Megabytes/sec per drive | Permanent air-gapped national satellite payload archive |

---

### 5. Cryptographic Security Enclave & Network Hardware

#### 5.1 Command Enclave Cryptographic Hardware
* **Hardware Security Modules (HSM)**: Dual Thales Luna HSM 7 (FIPS 140-3 Level 3 certified) installed in tamper-evident server racks.
* **Smart Card / YubiKey Authenticators**: YubiKey 5 Series FIPS tokens required for physical insertion by Mission Director and FDO during telecommand sign-off.

#### 5.2 Unidirectional Optical Data Diodes
* **Hardware Diodes**: Advenica SecuriCDS / OWL Cyber Defense 10Gbps Hardware Data Diodes.
* **Function**: Physically enforces ONE-WAY data flow from air-gapped Mission Control to DMZ cloud portal, ensuring zero inbound TCP connection can reach C2 networks.

```
[ Air-Gapped Core C2 Network ] ---> ( Optical Transmitter ) ---+
                                                              |
                                                    ( Fiber Optic Strand )
                                                              |
[ Cloud DMZ Dissemination ]    <--- ( Optical Receiver ) -----+
```

#### 5.3 Power & Network Redundancy
* **Core Network Switches**: Spine-Leaf Architecture with Arista 7060X4 32x 100GbE Switches.
* **Firewalls**: High-Availability Pair of Palo Alto PA-5450 Next-Gen Firewalls.
* **Uninterruptible Power Supply (UPS)**: 300 kVA Dual-Redundant Online UPS with Lithium-ion Battery Banks providing 45 minutes of full-load backup, backed by twin 750 kVA Diesel Generators with automatic transfer switches (ATS).
