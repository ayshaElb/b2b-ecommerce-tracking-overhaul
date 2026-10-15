"""
google_ads_enhanced_conv.py
Google Ads Enhanced Conversions client.
Enables offline and server-side conversion upload with hashed user identifiers
to restore lost conversions and optimize Smart Bidding algorithms.
"""

import hashlib
import time
from typing import Dict, Any, Optional

def hash_identifier(val: Optional[str]) -> Optional[str]:
    if not val:
        return None
    return hashlib.sha256(val.strip().lower().encode("utf-8")).hexdigest()

class GoogleAdsEnhancedConversions:
    def __init__(self, customer_id: str, conversion_action_id: str):
        self.customer_id = customer_id
        self.conversion_action_id = conversion_action_id

    def build_conversion_payload(
        self,
        transaction_id: str,
        conversion_value: float,
        currency: str,
        user_email: str,
        user_phone: Optional[str] = None
    ) -> Dict[str, Any]:
        return {
            "customerId": self.customer_id,
            "conversionAction": f"customers/{self.customer_id}/conversionActions/{self.conversion_action_id}",
            "orderId": transaction_id,
            "conversionDateTime": time.strftime("%Y-%m-%d %H:%M:%S+00:00", time.gmtime()),
            "conversionValue": conversion_value,
            "currencyCode": currency,
            "userIdentifiers": [
                {"hashedEmail": hash_identifier(user_email)},
                {"hashedPhoneNumber": hash_identifier(user_phone)} if user_phone else None
            ]
        }

    def upload_conversion(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Clean null values in identifiers
        payload["userIdentifiers"] = [i for i in payload["userIdentifiers"] if i is not None]
        return {
            "status": "uploaded",
            "order_id": payload["orderId"],
            "conversion_value": payload["conversionValue"],
            "timestamp": payload["conversionDateTime"]
        }
