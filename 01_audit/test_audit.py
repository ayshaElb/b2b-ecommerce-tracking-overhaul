import pytest
from audit_tracking_discrepancies import TrackingAuditor

def test_tracking_auditor():
    bo_orders = [{"order_id": f"ORD-{i}", "amount": 100.0} for i in range(1, 11)]
    # 6 capturees, 2 dupliquees
    events = [{"event_name": "purchase", "transaction_id": f"ORD-{i}", "value": 100.0} for i in range(1, 7)]
    events.append({"event_name": "purchase", "transaction_id": "ORD-1", "value": 100.0})

    auditor = TrackingAuditor(bo_orders, events)
    summary = auditor.run_audit()

    assert summary.total_backoffice_orders == 10
    assert summary.total_client_ga4_purchases == 7
    assert summary.data_loss_percentage == 40.0
    assert summary.duplicate_conversions == 1
