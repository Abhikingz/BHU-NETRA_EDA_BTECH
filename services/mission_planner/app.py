"""
BHU-NETRA: Mission Planning & Pass Scheduler Microservice
Zero-dependency Python standard library implementation.
"""

import json
import datetime
import uuid
from wsgiref.simple_server import make_server

SATELLITES = ["NETRA-EO-01", "NETRA-EO-02", "NETRA-SAR-01"]
GROUND_STATIONS = ["GS-SHADNAGAR-01", "GS-PORTBLAIR-02", "GS-SVALBARD-01"]

def application(environ, start_response):
    path = environ.get('PATH_INFO', '')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    if path == '/health':
        response_data = {"service": "mission_planner", "status": "UP", "timestamp": datetime.datetime.utcnow().isoformat() + "Z"}
        start_response('200 OK', [('Content-Type', 'application/json')])
        return [json.dumps(response_data).encode('utf-8')]
        
    elif path == '/api/v1/planning/passes/schedule' and method == 'POST':
        try:
            length = int(environ.get('CONTENT_LENGTH', '0'))
            body = environ['wsgi.input'].read(length) if length > 0 else b'{}'
            data = json.loads(body.decode('utf-8'))
        except Exception:
            data = {}
            
        start_time = data.get("planning_window_start", datetime.datetime.utcnow().isoformat() + "Z")
        end_time = data.get("planning_window_end", (datetime.datetime.utcnow() + datetime.timedelta(days=1)).isoformat() + "Z")
        schedule_id = f"SCH-{datetime.datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
        
        passes = []
        base_time = datetime.datetime.utcnow()
        for idx, sat in enumerate(SATELLITES):
            gs = GROUND_STATIONS[idx % len(GROUND_STATIONS)]
            aos = base_time + datetime.timedelta(hours=idx * 2, minutes=15)
            los = aos + datetime.timedelta(minutes=11, seconds=42)
            passes.append({
                "pass_id": f"PASS-{sat[:7]}-{gs[3:7]}-{uuid.uuid4().hex[:4].upper()}",
                "satellite_id": sat,
                "ground_station_id": gs,
                "aos_time": aos.isoformat() + "Z",
                "los_time": los.isoformat() + "Z",
                "max_elevation_deg": round(65.4 + (idx * 5), 1),
                "task_type": "PAYLOAD_DOWNLINK_AND_TELEMETRY"
            })
            
        response_data = {
            "schedule_id": schedule_id,
            "status": "GENERATED",
            "planning_window": {"start": start_time, "end": end_time},
            "total_passes": len(passes),
            "passes": passes
        }
        start_response('200 OK', [('Content-Type', 'application/json')])
        return [json.dumps(response_data).encode('utf-8')]
        
    elif path == '/api/v1/planning/tasking/emergency' and method == 'POST':
        try:
            length = int(environ.get('CONTENT_LENGTH', '0'))
            body = environ['wsgi.input'].read(length) if length > 0 else b'{}'
            data = json.loads(body.decode('utf-8'))
        except Exception:
            data = {}
            
        requestor = data.get("requestor", "NDRF_DISASTER_OPS")
        event_type = data.get("event_type", "FLOOD_MONITORING")
        preempted_pass_id = f"PASS-NETRA-PREEMPT-{uuid.uuid4().hex[:4].upper()}"
        
        response_data = {
            "status": "ACCEPTED_AND_PREEMPTED",
            "emergency_requestor": requestor,
            "event_type": event_type,
            "preempted_routine_passes": [preempted_pass_id],
            "allocated_pass": {
                "pass_id": f"PASS-EMERGENCY-{uuid.uuid4().hex[:6].upper()}",
                "satellite_id": "NETRA-EO-01",
                "ground_station_id": "GS-SHADNAGAR-01",
                "priority": "CRITICAL_OVERRIDE_LEVEL_1",
                "target_aoi": data.get("target_aoi", {"type": "Polygon", "coordinates": [[[85.2, 19.8], [86.5, 19.8], [86.5, 20.9], [85.2, 20.9], [85.2, 19.8]]]}),
                "status": "SCHEDULED_IMMEDIATE"
            }
        }
        start_response('202 Accepted', [('Content-Type', 'application/json')])
        return [json.dumps(response_data).encode('utf-8')]
        
    else:
        start_response('404 Not Found', [('Content-Type', 'application/json')])
        return [json.dumps({"error": "Endpoint not found"}).encode('utf-8')]

if __name__ == '__main__':
    print("Starting BHU-NETRA Mission Planner Service on http://0.0.0.0:5001...")
    with make_server('0.0.0.0', 5001, application) as httpd:
        httpd.serve_forever()
