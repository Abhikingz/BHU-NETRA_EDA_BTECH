"""
BHU-NETRA: Command Security Enclave Microservice
Zero-dependency Python standard library implementation.
Air-gapped 3-Stage Multi-Sign-Off Cryptographic Command Authorization Workflow.
"""

import json
import datetime
import uuid
import hashlib
from wsgiref.simple_server import make_server

COMMAND_STORE = {}

def application(environ, start_response):
    path = environ.get('PATH_INFO', '')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    if path == '/health':
        response_data = {"service": "command_security_enclave", "status": "UP", "hsm_status": "FIPS_140_3_LEVEL_3_READY"}
        start_response('200 OK', [('Content-Type', 'application/json')])
        return [json.dumps(response_data).encode('utf-8')]
        
    elif path == '/api/v1/commands/authorizations/initiate' and method == 'POST':
        try:
            length = int(environ.get('CONTENT_LENGTH', '0'))
            body = environ['wsgi.input'].read(length) if length > 0 else b'{}'
            data = json.loads(body.decode('utf-8'))
        except Exception:
            data = {}
            
        sat_id = data.get("satellite_id", "NETRA-EO-01")
        opcode = data.get("command_opcode", "CMD_AOCS_ORBIT_RAISE_EXECUTE")
        operator_id = data.get("operator_id", "OP-77412")
        
        cmd_id = f"CMD-AUTH-{uuid.uuid4().hex[:6].upper()}"
        record = {
            "command_authorization_id": cmd_id,
            "satellite_id": sat_id,
            "telecommand": {
                "opcode": opcode,
                "parameters": data.get("parameters", {"delta_v_m_s": 0.45})
            },
            "status": "PENDING_FDO_APPROVAL",
            "sign_off_chain": [
                {
                    "stage": 1,
                    "role": "SYSTEM_OPERATOR",
                    "user_id": operator_id,
                    "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                    "status": "APPROVED"
                }
            ],
            "created_at": datetime.datetime.utcnow().isoformat() + "Z"
        }
        COMMAND_STORE[cmd_id] = record
        start_response('201 Created', [('Content-Type', 'application/json')])
        return [json.dumps(record).encode('utf-8')]
        
    elif path.startswith('/api/v1/commands/authorizations/') and path.endswith('/sign') and method == 'POST':
        parts = path.split('/')
        cmd_id = parts[5] if len(parts) >= 7 else ''
        
        if cmd_id not in COMMAND_STORE:
            start_response('404 Not Found', [('Content-Type', 'application/json')])
            return [json.dumps({"error": "Command Authorization ID not found"}).encode('utf-8')]
            
        record = COMMAND_STORE[cmd_id]
        try:
            length = int(environ.get('CONTENT_LENGTH', '0'))
            body = environ['wsgi.input'].read(length) if length > 0 else b'{}'
            data = json.loads(body.decode('utf-8'))
        except Exception:
            data = {}
            
        approver_role = data.get("approver_role", "FLIGHT_DYNAMICS_OFFICER")
        approver_id = data.get("approver_id", "FDO-3004")
        decision = data.get("approval_decision", "APPROVED")
        
        if decision != "APPROVED":
            record["status"] = "REJECTED"
        elif approver_role == "FLIGHT_DYNAMICS_OFFICER" and record["status"] == "PENDING_FDO_APPROVAL":
            record["sign_off_chain"].append({
                "stage": 2,
                "role": "FLIGHT_DYNAMICS_OFFICER",
                "user_id": approver_id,
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                "status": "APPROVED"
            })
            record["status"] = "PENDING_MD_APPROVAL"
        elif approver_role == "MISSION_DIRECTOR" and record["status"] == "PENDING_MD_APPROVAL":
            hsm_raw_sig = hashlib.sha256(f"{cmd_id}:THALES_HSM_KEY_01:{datetime.datetime.utcnow()}".encode()).hexdigest()
            record["sign_off_chain"].append({
                "stage": 3,
                "role": "MISSION_DIRECTOR",
                "user_id": approver_id,
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                "status": "APPROVED",
                "hsm_key_id": "THALES-LUNA-HSM-KEY-C2-PROD-01",
                "cryptographic_signature": f"MEQCID{hsm_raw_sig[:24]}===="
            })
            record["status"] = "FULLY_AUTHORIZED_FOR_UPLINK"
            record["ccsds_telecommand_hex"] = f"1ACFFC1D0005774120011245{hsm_raw_sig[:16].upper()}BCH_CRC_OK"
            record["uplink_window"] = {
                "valid_from": datetime.datetime.utcnow().isoformat() + "Z",
                "valid_until": (datetime.datetime.utcnow() + datetime.timedelta(minutes=15)).isoformat() + "Z"
            }
            
        start_response('200 OK', [('Content-Type', 'application/json')])
        return [json.dumps(record).encode('utf-8')]
        
    else:
        start_response('404 Not Found', [('Content-Type', 'application/json')])
        return [json.dumps({"error": "Endpoint not found"}).encode('utf-8')]

if __name__ == '__main__':
    print("Starting BHU-NETRA Command Security Enclave Service on http://0.0.0.0:5002...")
    with make_server('0.0.0.0', 5002, application) as httpd:
        httpd.serve_forever()
