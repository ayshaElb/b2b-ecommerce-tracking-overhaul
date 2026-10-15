"""
deduplicator.py
In-memory deduplication engine ensuring client-side pixel hits and
server-side CAPI/MP hits share the exact same event_id.
Prevents duplicate conversions while guaranteeing redundancy if client hit fails.
"""

import time
from typing import Dict, Any, Optional

class DeduplicationEngine:
    def __init__(self, ttl_seconds: int = 86400):
        # Stores event_id -> {first_seen: timestamp, sources: set()}
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl_seconds

    def process_incoming_hit(self, event_id: str, source: str) -> Dict[str, Any]:
        """
        source: 'browser_pixel' or 'server_capi'
        Returns action: 'accept' (new hit) or 'deduplicate' (already registered)
        """
        now = time.time()
        
        # Clean expired
        expired = [k for k, v in self._cache.items() if now - v["first_seen"] > self.ttl]
        for k in expired:
            del self._cache[k]

        if event_id not in self._cache:
            self._cache[event_id] = {
                "first_seen": now,
                "sources": {source}
            }
            return {
                "action": "forward",
                "is_duplicate": False,
                "first_source": source,
                "message": f"First time event {event_id} is seen from {source}"
            }
        else:
            entry = self._cache[event_id]
            entry["sources"].add(source)
            return {
                "action": "deduplicate",
                "is_duplicate": True,
                "primary_source": list(entry["sources"])[0],
                "message": f"Duplicate event {event_id} recognized and merged (sources: {entry['sources']})"
            }
