"""
Spendwise AI Tool: report_exporter
Gathers and aggregates full deterministic audit evidence into a structured export bundle.
"""

from typing import Dict, Any, Optional
from database.repository import Repository
from .spending_analytics import execute as spending_analytics
from .anomaly_detector import execute as anomaly_detector
from .duplicate_finder import execute as duplicate_finder
from .recurring_detector import execute as recurring_detector
from .refund_matcher import execute as refund_matcher
from .budget_simulator import execute as budget_simulator

def execute(
    repository: Optional[Repository] = None
) -> Dict[str, Any]:
    repo = repository or Repository()
    
    analytics = spending_analytics(repository=repo)
    anomalies = anomaly_detector(repository=repo)
    duplicates = duplicate_finder(repository=repo)
    recurring = recurring_detector(repository=repo)
    recoveries = refund_matcher(repository=repo)
    budget = budget_simulator(repository=repo)

    return {
        "status": "success",
        "audit_bundle": {
            "analytics": analytics,
            "anomalies": anomalies,
            "duplicate_candidates": duplicates,
            "recurring_subscriptions": recurring,
            "recoveries": recoveries,
            "budget_baseline": budget
        },
        "summary": (
            f"Audit summary generated: {analytics.get('total_lifetime_expense')} lifetime spend, "
            f"{anomalies.get('anomaly_count')} anomalies flagged, {duplicates.get('candidate_count')} duplicate candidates, "
            f"{recurring.get('recurring_count')} subscriptions detected, "
            f"₹{recoveries.get('total_confirmed_recovery')} confirmed recovered (₹{recoveries.get('total_unresolved_recovery')} unresolved)."
        )
    }

