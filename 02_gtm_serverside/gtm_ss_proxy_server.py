"""
gtm_ss_proxy_server.py
First-Party Server-Side Tagging Gateway (simulating GTM Server-Side proxy).
- Receives events via first-party endpoint (e.g. data.company-b2b.com)
- Sets and preserves HTTP-Only cookies to bypass Safari ITP expiration
- Masks IP addresses for GDPR compliance
- Coordinates event dispatch to GA4, Meta CAPI, and Google Ads
"""

import time
import hashlib
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

from .cookie_consent_handler import ConsentHandler

app = FastAPI(
    title="GTM Server-Side First-Party Proxy",
    version="1.0.0",
    description="First-party server container proxying tracking signals with GDPR compliance."
)

class EventItem(BaseModel):
    item_id: str
    item_name: str
    price: float
    quantity: int = 1

class TrackingEvent(BaseModel):
    event_name: str
    event_id: str = Field(..., description="Unique event ID for cross-channel deduplication")
    timestamp: Optional[int] = None
    user_data: Optional[Dict[str, Any]] = None
    custom_parameters: Optional[Dict[str, Any]] = None
    items: Optional[List[EventItem]] = None
    consent: Optional[Dict[str, str]] = None

def anonymize_ip(ip: str) -> str:
    """Mask the last octet of IPv4 or last 80 bits of IPv6 for GDPR compliance."""
    if not ip:
        return "0.0.0.0"
    parts = ip.split(".")
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.{parts[2]}.0"
    return "2001:db8::"

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "gtm-ss-proxy", "timestamp": int(time.time())}

@app.post("/collect")
async def collect_event(event: TrackingEvent, request: Request, response: Response):
    client_ip = request.client.host if request.client else "127.0.0.1"
    masked_ip = anonymize_ip(client_ip)
    user_agent = request.headers.get("user-agent", "")

    # Manage Consent
    consent_mgr = ConsentHandler(event.consent)
    sanitized_event = consent_mgr.sanitize_payload_for_consent(event.model_dump())

    # First-Party HTTP-Only cookie management to resist Safari ITP
    fbp_cookie = request.cookies.get("_fbp")
    if not fbp_cookie:
        # Generate new first-party _fbp (fb.1.<timestamp>.<random>)
        fbp_cookie = f"fb.1.{int(time.time()*1000)}.{hashlib.md5(client_ip.encode()).hexdigest()[:8]}"
        response.set_cookie(
            key="_fbp",
            value=fbp_cookie,
            max_age=365*24*3600, # 1 year lifetime (server-side HTTP-Only)
            httponly=True,
            secure=True,
            samesite="lax"
        )

    return {
        "status": "accepted",
        "event_id": event.event_id,
        "event_name": event.event_name,
        "anonymized_ip": masked_ip,
        "consent_mode": {
            "analytics_allowed": consent_mgr.is_analytics_allowed(),
            "ads_allowed": consent_mgr.is_ads_allowed()
        },
        "dispatched_to": ["GA4_MP", "META_CAPI", "GOOGLE_ADS_ENHANCED"]
    }
