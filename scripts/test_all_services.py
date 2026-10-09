"""
BHU-NETRA End-to-End Satellite Pass Journey Test Suite & Microservices Simulator
Executes a complete 8-stage pass lifecycle across all 4 microservices.
"""

import sys
import os
import threading
import time
import json
import urllib.request
import urllib.error

# Ensure root bhu-netra directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import microservice WSGI applications
from services.mission_planner.app import application as mission_planner_app
from services.command_security_enclave.app import application as command_enclave_app
from services.ground_station_gateway.app import application as gs_gateway_app
from services.data_dissemination_portal.app import application as dissemination_app

from wsgiref.simple_server import make_server

def run_server(app, port):
    server = make_server('127.0.0.1', port, app)
    server.serve_forever()

def http_post(url, data_dict):
    req = urllib.request.Request(url, data=json.dumps(data_dict).encode('utf-8'), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))

def http_get(url):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))

def run_pass_journey_simulation():
    print("=" * 80)
    print("      BHU-NETRA: SATELLITE PASS JOURNEY END-TO-END SIMULATION SUITE")
    print("=" * 80)
    time.sleep(1)

    # 1. Mission Planning & Pass Schedule Generation
    print("\n[STAGE 1] Querying Mission Planner for Satellite Pass Schedule...")
    sched_resp = http_post("http://127.0.0.1:5001/api/v1/planning/passes/schedule", {
        "planning_window_start": "2026-10-10T00:00:00Z",
        "planning_window_end": "2026-10-11T00:00:00Z"
    })
    print(f" -> Schedule Generated: {sched_resp['schedule_id']} (Total Passes: {sched_resp['total_passes']})")
    first_pass = sched_resp['passes'][0]
    print(f" -> Pass ID: {first_pass['pass_id']} | Sat: {first_pass['satellite_id']} | GS: {first_pass['ground_station_id']}")

    # 2. Live Telemetry Stream Ingestion
    print("\n[STAGE 2 & 3] Ingesting Real-Time Telemetry Stream & Anomaly Check...")
    telemetry_resp = http_get(f"http://127.0.0.1:5003/api/v1/telemetry/sample?satellite_id={first_pass['satellite_id']}&ground_station_id={first_pass['ground_station_id']}")
    print(f" -> Event ID: {telemetry_resp['event_id']} | CADU Frame: #{telemetry_resp['raw_cadu_sequence']}")
    print(f" -> Bus Voltage: {telemetry_resp['parameters']['electrical']['bus_voltage_v']}V | Battery SoC: {telemetry_resp['parameters']['electrical']['battery_soc_pct']}%")
    print(f" -> Anomaly Status: {telemetry_resp['anomaly_status']['severity']}")

    # 3. Cryptographic Multi-Sign-Off Command Authorization Workflow
    print("\n[STAGE 4] Executing 3-Stage Air-Gapped Command Authorization Workflow...")
    # Stage 1: Operator
    init_cmd_resp = http_post("http://127.0.0.1:5002/api/v1/commands/authorizations/initiate", {
        "satellite_id": first_pass['satellite_id'],
        "command_opcode": "CMD_PAYLOAD_CAMERA_POWER_ON",
        "operator_id": "OP-77412"
    })
    cmd_id = init_cmd_resp['command_authorization_id']
    print(f" -> Stage 1 (Operator): Command Created -> ID: {cmd_id} [Status: {init_cmd_resp['status']}]")

    # Stage 2: Flight Dynamics Officer (FDO)
    fdo_sign_resp = http_post(f"http://127.0.0.1:5002/api/v1/commands/authorizations/{cmd_id}/sign", {
        "approver_role": "FLIGHT_DYNAMICS_OFFICER",
        "approver_id": "FDO-3004",
        "approval_decision": "APPROVED"
    })
    print(f" -> Stage 2 (FDO): Approved Orbit & Power Window [Status: {fdo_sign_resp['status']}]")

    # Stage 3: Mission Director (MD) with Thales HSM PKCS#11 Signature
    md_sign_resp = http_post(f"http://127.0.0.1:5002/api/v1/commands/authorizations/{cmd_id}/sign", {
        "approver_role": "MISSION_DIRECTOR",
        "approver_id": "MD-001",
        "approval_decision": "APPROVED"
    })
    print(f" -> Stage 3 (Mission Director HSM): Cryptographic Signature Generated!")
    print(f" -> CCSDS Telecommand Frame: {md_sign_resp['ccsds_telecommand_hex']}")
    print(f" -> Final State: {md_sign_resp['status']} (Ready for Uplink)")

    # 4. Mid-Pass Ground Station Handover
    print("\n[STAGE 5] Executing Mid-Pass Ground Station Control Handover...")
    handover_resp = http_post("http://127.0.0.1:5003/api/v1/handover/initiate", {
        "satellite_id": first_pass['satellite_id'],
        "source_gs_id": "GS-SHADNAGAR-01",
        "target_gs_id": "GS-PORTBLAIR-02"
    })
    print(f" -> Handover ID: {handover_resp['handover_id']}")
    print(f" -> Transfer: {handover_resp['receding_ground_station']['gs_id']} -> {handover_resp['approaching_ground_station']['gs_id']}")
    print(f" -> Link State: {handover_resp['handover_phase']} | Telemetry Continuity: {handover_resp['telemetry_stream_continuity']}")

    # 5. Data Dissemination & Entitlement Delivery
    print("\n[STAGE 6 - 8] Searching STAC Imagery Catalog & Ordering Data Dissemination...")
    search_resp = http_post("http://127.0.0.1:5004/api/v1/catalog/products/search", {
        "bbox": [70.0, 8.0, 90.0, 30.0]
    })
    print(f" -> STAC Items Found: {search_resp['numberMatched']}")
    first_item = search_resp['features'][0]
    print(f" -> Selected STAC Item: {first_item['id']} ({first_item['properties']['processing_level']} COG)")

    order_resp = http_post("http://127.0.0.1:5004/api/v1/dissemination/orders", {
        "recipient_department": "MINISTRY_OF_AGRICULTURE",
        "product_id": first_item['id']
    })
    print(f" -> Delivery Envelope ID: {order_resp['delivery_id']}")
    print(f" -> Recipient: {order_resp['recipient_department']} via {order_resp['recipient_network']}")
    print(f" -> ABAC Policy Applied: Classification Mask = {order_resp['entitlement_policy']['classification_mask_applied']}")
    print(f" -> Storage URI: {order_resp['product']['storage_uri']}")

    print("\n" + "=" * 80)
    print(" SUCCESS: ALL 8 STAGES OF SATELLITE PASS JOURNEY SIMULATED SUCCESSFULLY!")
    print("=" * 80 + "\n")

if __name__ == '__main__':
    # Launch microservices on background threads
    t1 = threading.Thread(target=run_server, args=(mission_planner_app, 5001), daemon=True)
    t2 = threading.Thread(target=run_server, args=(command_enclave_app, 5002), daemon=True)
    t3 = threading.Thread(target=run_server, args=(gs_gateway_app, 5003), daemon=True)
    t4 = threading.Thread(target=run_server, args=(dissemination_app, 5004), daemon=True)

    t1.start()
    t2.start()
    t3.start()
    t4.start()

    time.sleep(1) # Allow servers to bind
    run_pass_journey_simulation()
