"""
cookie_consent_handler.py
Handles Google Consent Mode v2 & GDPR compliance rules:
- analytics_storage
- ad_storage
- ad_user_data
- ad_personalization
"""

from typing import Dict, Any, Optional

class ConsentHandler:
    def __init__(self, consent_state: Optional[Dict[str, str]] = None):
        self.consent = consent_state or {
            "analytics_storage": "denied",
            "ad_storage": "denied",
            "ad_user_data": "denied",
            "ad_personalization": "denied"
        }

    def is_analytics_allowed(self) -> bool:
        return self.consent.get("analytics_storage") == "granted"

    def is_ads_allowed(self) -> bool:
        return (
            self.consent.get("ad_storage") == "granted" and
            self.consent.get("ad_user_data") == "granted"
        )

    def sanitize_payload_for_consent(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Strip PII and marketing cookies if user refused ad consent."""
        sanitized = payload.copy()
        user_data = sanitized.get("user_data", {})

        if not self.is_ads_allowed():
            # Strip PII according to GDPR Consent rules
            sanitized["user_data"] = {
                k: v for k, v in user_data.items()
                if k not in ["email", "phone", "first_name", "last_name", "fbc"]
            }
        
        return sanitized
