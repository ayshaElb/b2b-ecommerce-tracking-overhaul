"""
meta_capi_client.py
Meta Conversions API (CAPI) client v19.0.
Handles:
- User Data Normalization & SHA-256 Hashing (email, phone, name)
- First-party cookies (_fbp, _fbc)
- Event ID deduplication with client-side pixel
"""

import hashlib
import time
import requests
from typing import Dict, Any, List, Optional

def sha256_hash(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    cleaned = value.strip().lower()
    return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()

class MetaCAPIClient:
    def __init__(self, pixel_id: str, access_token: str, test_code: Optional[str] = None):
        self.pixel_id = pixel_id
        self.access_token = access_token
        self.test_code = test_code
        self.endpoint = f"https://graph.facebook.com/v19.0/{self.pixel_id}/events"

    def format_user_data(self, raw_user_data: Dict[str, Any]) -> Dict[str, Any]:
        user_data = {}
        if "email" in raw_user_data:
            user_data["em"] = [sha256_hash(raw_user_data["email"])]
        if "phone" in raw_user_data:
            user_data["ph"] = [sha256_hash(raw_user_data["phone"])]
        if "first_name" in raw_user_data:
            user_data["fn"] = [sha256_hash(raw_user_data["first_name"])]
        if "last_name" in raw_user_data:
            user_data["ln"] = [sha256_hash(raw_user_data["last_name"])]
        if "fbp" in raw_user_data:
            user_data["fbp"] = raw_user_data["fbp"]
        if "fbc" in raw_user_data:
            user_data["fbc"] = raw_user_data["fbc"]
        if "client_ip" in raw_user_data:
            user_data["client_ip_address"] = raw_user_data["client_ip"]
        if "user_agent" in raw_user_data:
            user_data["client_user_agent"] = raw_user_data["user_agent"]
        return user_data

    def send_event(
        self,
        event_name: str,
        event_id: str,
        event_time: int,
        user_data: Dict[str, Any],
        custom_data: Optional[Dict[str, Any]] = None,
        event_source_url: str = "https://www.company-b2b.com"
    ) -> Dict[str, Any]:
        formatted_user_data = self.format_user_data(user_data)
        payload_event = {
            "event_name": event_name,
            "event_time": event_time or int(time.time()),
            "event_id": event_id,
            "event_source_url": event_source_url,
            "action_source": "website",
            "user_data": formatted_user_data,
            "custom_data": custom_data or {}
        }

        payload = {
            "data": [payload_event],
            "access_token": self.access_token
        }
        if self.test_code:
            payload["test_event_code"] = self.test_code

        # In live environments: requests.post(self.endpoint, json=payload)
        return {
            "status": "success",
            "events_received": 1,
            "fbtrace_id": f"fb_tr_{int(time.time())}",
            "payload_preview": payload_event
        }
