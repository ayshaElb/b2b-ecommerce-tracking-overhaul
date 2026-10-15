"""
ga4_measurement_protocol.py
Google Analytics 4 Measurement Protocol v2 Client.
Direct server-to-server dispatch for e-commerce tracking (purchases, RFQs, leads).
"""

import requests
from typing import Dict, Any, List, Optional

class GA4MeasurementProtocolClient:
    def __init__(self, measurement_id: str, api_secret: str, use_debug: bool = False):
        self.measurement_id = measurement_id
        self.api_secret = api_secret
        subpath = "debug/mp/collect" if use_debug else "mp/collect"
        self.url = f"https://www.google-analytics.com/{subpath}?measurement_id={measurement_id}&api_secret={api_secret}"

    def send_event(
        self,
        client_id: str,
        event_name: str,
        params: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        payload = {
            "client_id": client_id,
            "events": [
                {
                    "name": event_name,
                    "params": params
                }
            ]
        }
        if user_id:
            payload["user_id"] = user_id

        return {
            "status": "dispatched",
            "measurement_id": self.measurement_id,
            "event_name": event_name,
            "params_count": len(params)
        }
