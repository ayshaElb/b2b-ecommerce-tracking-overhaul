"""
event_dispatcher.py
Dispatches incoming e-commerce tracking events simultaneously to:
- Google Analytics 4 (Measurement Protocol)
- Meta Conversions API (CAPI)
- Google Ads Enhanced Conversions
"""

from typing import Dict, Any
from .meta_capi_client import MetaCAPIClient
from .google_ads_enhanced_conv import GoogleAdsEnhancedConversions
from .ga4_measurement_protocol import GA4MeasurementProtocolClient

class EventDispatcher:
    def __init__(
        self,
        meta_client: MetaCAPIClient,
        gads_client: GoogleAdsEnhancedConversions,
        ga4_client: GA4MeasurementProtocolClient
    ):
        self.meta = meta_client
        self.gads = gads_client
        self.ga4 = ga4_client

    def dispatch_purchase(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        event_id = event_data["event_id"]
        tx_id = event_data.get("transaction_id", event_id)
        user_info = event_data.get("user_data", {})
        value = event_data.get("value", 0.0)
        currency = event_data.get("currency", "EUR")

        # 1. Meta CAPI
        meta_res = self.meta.send_event(
            event_name="Purchase",
            event_id=event_id,
            event_time=event_data.get("timestamp", 0),
            user_data=user_info,
            custom_data={"value": value, "currency": currency}
        )

        # 2. Google Ads
        gads_payload = self.gads.build_conversion_payload(
            transaction_id=tx_id,
            conversion_value=value,
            currency=currency,
            user_email=user_info.get("email", ""),
            user_phone=user_info.get("phone", "")
        )
        gads_res = self.gads.upload_conversion(gads_payload)

        # 3. GA4 MP
        ga4_res = self.ga4.send_event(
            client_id=user_info.get("client_id", "anon_client"),
            event_name="purchase",
            params={
                "transaction_id": tx_id,
                "value": value,
                "currency": currency,
                "event_id": event_id
            }
        )

        return {
            "event_id": event_id,
            "meta_capi": meta_res["status"],
            "google_ads": gads_res["status"],
            "ga4_mp": ga4_res["status"]
        }
