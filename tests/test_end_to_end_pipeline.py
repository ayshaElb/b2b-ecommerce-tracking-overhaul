"""
test_end_to_end_pipeline.py
Unit tests for the B2B tracking pipeline using importlib for numbered package loading.
"""

import sys
import os
import unittest
import importlib

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, base_dir)

consent_mod = importlib.import_module("02_gtm_serverside.cookie_consent_handler")
meta_mod = importlib.import_module("03_conversions_api.meta_capi_client")
gads_mod = importlib.import_module("03_conversions_api.google_ads_enhanced_conv")
ga4_mod = importlib.import_module("03_conversions_api.ga4_measurement_protocol")
dispatcher_mod = importlib.import_module("03_conversions_api.event_dispatcher")
dedup_mod = importlib.import_module("04_deduplication_engine.deduplicator")
val_mod = importlib.import_module("04_deduplication_engine.validation_suite")

ConsentHandler = consent_mod.ConsentHandler
MetaCAPIClient = meta_mod.MetaCAPIClient
sha256_hash = meta_mod.sha256_hash
GoogleAdsEnhancedConversions = gads_mod.GoogleAdsEnhancedConversions
GA4MeasurementProtocolClient = ga4_mod.GA4MeasurementProtocolClient
EventDispatcher = dispatcher_mod.EventDispatcher
DeduplicationEngine = dedup_mod.DeduplicationEngine
TrackingValidator = val_mod.TrackingValidator

class TestTrackingPipeline(unittest.TestCase):
    def test_consent_sanitization(self):
        handler = ConsentHandler({"ad_storage": "denied", "ad_user_data": "denied", "analytics_storage": "granted"})
        raw_payload = {
            "event_name": "purchase",
            "user_data": {
                "email": "buyer@procorp.com",
                "phone": "+33612345678",
                "client_id": "cid_999"
            }
        }
        sanitized = handler.sanitize_payload_for_consent(raw_payload)
        self.assertNotIn("email", sanitized["user_data"])
        self.assertNotIn("phone", sanitized["user_data"])
        self.assertEqual(sanitized["user_data"]["client_id"], "cid_999")

    def test_sha256_hashing(self):
        raw_email = "  Buyer.Contact@Enterprise.COM  "
        hashed = sha256_hash(raw_email)
        expected_hash = "9f21a9172a730060d6539cec35ae83cd08769c05783d28211f125c7be4849bd2"
        self.assertEqual(hashed, expected_hash)

    def test_deduplication_engine(self):
        engine = DeduplicationEngine(ttl_seconds=3600)
        event_id = "TX-2026-9901"

        res_browser = engine.process_incoming_hit(event_id, source="browser_pixel")
        self.assertFalse(res_browser["is_duplicate"])
        self.assertEqual(res_browser["action"], "forward")

        res_server = engine.process_incoming_hit(event_id, source="server_capi")
        self.assertTrue(res_server["is_duplicate"])
        self.assertEqual(res_server["action"], "deduplicate")

    def test_payload_validator(self):
        valid_payload = {
            "event_id": "EVT-100",
            "value": 450.0,
            "user_data": {"email": "test@pro.com"}
        }
        errors = TrackingValidator.validate_purchase_payload(valid_payload)
        self.assertEqual(len(errors), 0)

        invalid_payload = {
            "value": -10.0,
            "user_data": {}
        }
        errors_inv = TrackingValidator.validate_purchase_payload(invalid_payload)
        self.assertGreaterEqual(len(errors_inv), 2)

    def test_full_event_dispatch(self):
        meta = MetaCAPIClient(pixel_id="123456", access_token="token_xyz")
        gads = GoogleAdsEnhancedConversions(customer_id="123", conversion_action_id="456")
        ga4 = GA4MeasurementProtocolClient(measurement_id="G-123", api_secret="sec_123")
        dispatcher = EventDispatcher(meta, gads, ga4)

        test_event = {
            "event_id": "TX-E2E-001",
            "transaction_id": "TX-E2E-001",
            "value": 2400.0,
            "currency": "EUR",
            "user_data": {
                "email": "buyer@acme-corp.com",
                "phone": "+33123456789",
                "client_id": "ga_client_55"
            }
        }

        result = dispatcher.dispatch_purchase(test_event)
        self.assertEqual(result["meta_capi"], "success")
        self.assertEqual(result["google_ads"], "uploaded")
        self.assertEqual(result["ga4_mp"], "dispatched")

if __name__ == "__main__":
    unittest.main()
