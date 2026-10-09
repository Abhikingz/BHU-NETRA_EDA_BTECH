"""
BHU-NETRA: Ground Station SDR Gateway & Handover Controller
Zero-dependency Python standard library implementation.
Simulates real-time telemetry frame ingestion, baseband link state, and mid-pass ground station handovers.
"""

import json
import datetime
import random
import uuid
from wsgiref.simple_server import make_server
from urllib.parse import parse_qs

ACTIVE_LINKS = {
    "GS-SHADNAGAR-01": {"status": "ONLINE", "carrier_lock": True, "sdr_mode": "VITA_49"},
    "GS-PORTBLAIR-02": {"status": "ONLINE", "carrier_lock": True, "sdr_mode": "VITA_49"},
    "GS-SVALBARD-01": {"status": "ONLINE", "carrier_lock": False, "sdr_mode": "LEGACY_PCM_FM"}
}

def application(environ, start_response):
    path = environ.get('PATH_INFO', '')
    method = environ.get('REQUEST_METHOD', 'GET')
    query_string = environ.get('QUERY_STRING', '')
    params = parse_qs(query_string)
    
    if path == '/health':
        response_data = {"service": "ground_station_gateway", "status": "UP", "active_ground_stations": len(ACTIVE_LINKS)}
        start_response('200 OK', [('Content-Type', 'application/json')])
        return [json.dumps(response_data).encode('utf-8')]
        
    elif path == '/api/v1/telemetry/sample' and method == 'GET':
        sat_id = params.get("satellite_id", ["NETRA-EO-01"])[0]
        gs_id = params.get("ground_station_id", ["GS-SHADNAGAR-01"])[0]
        
        bus_v = round(28.0 + random.uniform(-0.3, 0.4), 2)
        battery_soc = round(94.0 + random.uniform(-1.0, 2.0), 1)
        payload_temp = round(16.0 + random.uniform(-0.5, 0.8), 1)
        fuel_bar = round(14.8 + random.uniform(-0.02, 0.01), 2)
        has_anomaly = bus_v < 27.5 or payload_temp > 35.0
        
        telemetry_payload = {
            "event_id": f"TEL-EVT-{uuid.uuid4().hex[:8].upper()}",
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "satellite_id": sat_id,
            "ground_station_id": gs_id,
            "raw_cadu_sequence": random.randint(10000, 99999),
            "parameters": {
                "electrical": {
                    "bus_voltage_v": bus_v,
                    "solar_array_current_a": 18.5,
                    "battery_soc_pct": battery_soc
                },
                "thermal": {
                    "payload_camera_temp_c": payload_temp,
                    "battery_pack_temp_c": 21.0
                },
                "aocs": {
                    "quaternion": [0.0125, 0.9981, 0.0042, 0.0511],
                    "reaction_wheel_rpm": [1200, 1185, 1202, 0]
                },
                "propulsion": {
                    "fuel_pressure_bar": fuel_bar
                }
            },
            "anomaly_status": {
                "has_anomaly": has_anomaly,
                "severity": "CRITICAL_WARNING" if has_anomaly else "NOMINAL"
            }
        }
        start_response('200 OK', [('Content-Type', 'application/json')])
        return [json.dumps(telemetry_payload).encode('utf-8')]
        
    elif path == '/api/v1/handover/initiate' and method == 'POST':
        try:
            length = int(environ.get('CONTENT_LENGTH', '0'))
            body = environ['wsgi.input'].read(length) if length > 0 else b'{}'
            data = json.loads(body.decode('utf-8'))
        except Exception:
            data = {}
            
        sat_id = data.get("satellite_id", "NETRA-EO-01")
        src_gs = data.get("source_gs_id", "GS-SHADNAGAR-01")
        tgt_gs = data.get("target_gs_id", "GS-PORTBLAIR-02")
        handover_id = f"HO-{datetime.datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
        
        handover_result = {
            "handover_id": handover_id,
            "satellite_id": sat_id,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "receding_ground_station": {
                "gs_id": src_gs,
                "current_elevation_deg": 6.8,
                "rf_link_status": "RELEASE_CARRIER_LOCK"
            },
            "approaching_ground_station": {
                "gs_id": tgt_gs,
                "current_elevation_deg": 14.2,
                "rf_link_status": "ACQUIRED_CARRIER_LOCK"
            },
            "handover_phase": "PHASE_LOCK_SYNCHRONIZED_SUCCESS",
            "telemetry_stream_continuity": "ZERO_FRAME_LOSS",
            "active_c2_ground_station": tgt_gs
        }
        start_response('200 OK', [('Content-Type', 'application/json')])
        return [json.dumps(handover_result).encode('utf-8')]
        
    else:
        start_response('404 Not Found', [('Content-Type', 'application/json')])
        return [json.dumps({"error": "Endpoint not found"}).encode('utf-8')]

if __name__ == '__main__':
    print("Starting BHU-NETRA Ground Station SDR Gateway Service on http://0.0.0.0:5003...")
    with make_server('0.0.0.0', 5003, application) as httpd:
        httpd.serve_forever()
