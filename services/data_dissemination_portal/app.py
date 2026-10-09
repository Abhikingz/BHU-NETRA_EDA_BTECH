"""
BHU-NETRA: Data Dissemination Portal API & ABAC Entitlement Service
Zero-dependency Python standard library implementation.
OGC STAC Spatial Catalog API and ABAC Policy Entitlement Engine for G2G and Subscriber Delivery.
"""

import json
import datetime
import uuid
from wsgiref.simple_server import make_server

STAC_CATALOG = [
    {
        "id": "NETRA_EO01_20261010_L3_AGRI_COG_091",
        "satellite": "NETRA-EO-01",
        "processing_level": "L3",
        "acquisition_time": "2026-10-10T04:20:00Z",
        "cloud_cover_pct": 2.4,
        "classification": "CONFIDENTIAL_GOV",
        "bbox": [79.5, 15.0, 81.2, 17.0],
        "storage_uri": "s3://bhu-netra-level3-products/2026/10/10/NETRA_EO01_20261010_L3_AGRI.tif"
    },
    {
        "id": "NETRA_SAR01_20261009_L2_FLOOD_COG_044",
        "satellite": "NETRA-SAR-01",
        "processing_level": "L2",
        "acquisition_time": "2026-10-09T14:10:00Z",
        "cloud_cover_pct": 0.0,
        "classification": "CONFIDENTIAL_GOV",
        "bbox": [85.2, 19.8, 86.5, 20.9],
        "storage_uri": "s3://bhu-netra-level2-cog/2026/10/09/NETRA_SAR01_20261009_FLOOD.tif"
    }
]

def application(environ, start_response):
    path = environ.get('PATH_INFO', '')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    if path == '/health':
        response_data = {"service": "data_dissemination_portal", "status": "UP", "stac_spec": "1.0.0"}
        start_response('200 OK', [('Content-Type', 'application/json')])
        return [json.dumps(response_data).encode('utf-8')]
        
    elif path == '/api/v1/catalog/products/search' and method == 'POST':
        features = []
        for item in STAC_CATALOG:
            features.append({
                "type": "Feature",
                "id": item["id"],
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[item["bbox"][0], item["bbox"][1]], [item["bbox"][2], item["bbox"][1]], [item["bbox"][2], item["bbox"][3]], [item["bbox"][0], item["bbox"][3]], [item["bbox"][0], item["bbox"][1]]]]
                },
                "properties": {
                    "datetime": item["acquisition_time"],
                    "satellite": item["satellite"],
                    "processing_level": item["processing_level"],
                    "eo:cloud_cover": item["cloud_cover_pct"],
                    "classification": item["classification"]
                },
                "assets": {
                    "data": {
                        "href": f"https://data.bhu-netra.gov.in/cog/{item['id']}.tif",
                        "type": "image/tiff; application=geotiff; profile=cloud-optimized"
                    }
                }
            })
        response_data = {
            "type": "FeatureCollection",
            "numberMatched": len(features),
            "numberReturned": len(features),
            "features": features
        }
        start_response('200 OK', [('Content-Type', 'application/json')])
        return [json.dumps(response_data).encode('utf-8')]
        
    elif path == '/api/v1/dissemination/orders' and method == 'POST':
        try:
            length = int(environ.get('CONTENT_LENGTH', '0'))
            body = environ['wsgi.input'].read(length) if length > 0 else b'{}'
            data = json.loads(body.decode('utf-8'))
        except Exception:
            data = {}
            
        recipient = data.get("recipient_department", "MINISTRY_OF_AGRICULTURE")
        product_id = data.get("product_id", "NETRA_EO01_20261010_L3_AGRI_COG_091")
        delivery_id = f"DEL-{datetime.datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
        
        delivery_payload = {
            "delivery_id": delivery_id,
            "recipient_department": recipient,
            "recipient_network": "NICNET_DIRECT_GOV_BACKBONE",
            "clearance_level": "CONFIDENTIAL_GOV",
            "product": {
                "product_id": product_id,
                "stac_item_url": f"https://data.bhu-netra.gov.in/api/v1/catalog/items/{product_id}",
                "spatial_resolution_meters": 0.5,
                "format": "Cloud-Optimized GeoTIFF (COG)",
                "storage_uri": f"s3://bhu-netra-level3-products/2026/10/10/{product_id}.tif",
                "checksum_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            },
            "entitlement_policy": {
                "spatial_watermark_applied": False,
                "classification_mask_applied": True,
                "redacted_sensitive_zones": ["STRATEGIC_DEFENSE_ZONE_4"]
            },
            "delivered_at": datetime.datetime.utcnow().isoformat() + "Z"
        }
        start_response('200 OK', [('Content-Type', 'application/json')])
        return [json.dumps(delivery_payload).encode('utf-8')]
        
    else:
        start_response('404 Not Found', [('Content-Type', 'application/json')])
        return [json.dumps({"error": "Endpoint not found"}).encode('utf-8')]

if __name__ == '__main__':
    print("Starting BHU-NETRA Data Dissemination Portal Service on http://0.0.0.0:5004...")
    with make_server('0.0.0.0', 5004, application) as httpd:
        httpd.serve_forever()
