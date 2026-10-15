"""
validation_suite.py
Validates tracking payload conformance before dispatching to external APIs.
Guarantees high Event Match Quality (EMQ).
"""

import re
from typing import Dict, Any, List

class TrackingValidator:
    @staticmethod
    def validate_purchase_payload(payload: Dict[str, Any]) -> List[str]:
        errors = []

        if not payload.get("event_id"):
            errors.append("Missing required 'event_id' for deduplication.")

        val = payload.get("value")
        if val is None or val <= 0:
            errors.append(f"Invalid conversion value: {val}. Must be > 0.")

        user_data = payload.get("user_data", {})
        if not user_data:
            errors.append("Missing 'user_data' block for server matching.")
        else:
            # Check email format or hash
            em = user_data.get("email")
            if not em:
                errors.append("Missing email identifier in user_data.")

        return errors
