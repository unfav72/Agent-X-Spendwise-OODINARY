"""
Spendwise AI Tool: transaction_comparator
Compares financial metrics between two date periods or two months.
"""

from typing import Dict, Any, Optional
from database.repository import Repository

def execute(
    period_a_start: Optional[str] = None,
    period_a_end: Optional[str] = None,
    period_b_start: Optional[str] = None,
    period_b_end: Optional[str] = None,
    category: Optional[str] = None,
    repository: Optional[Repository] = None
) -> Dict[str, Any]:
    repo = repository or Repository()
    
    # If no periods supplied, default to comparing latest month vs previous month
    if not (period_a_start and period_b_start):
        overview = repo.get_spending_overview()
        monthly = overview.get("monthly_trend", [])
        if len(monthly) < 2:
            return {"status": "insufficient_data", "message": "At least two monthly periods needed for comparison."}
        m_curr = monthly[-1]["month"]
        m_prev = monthly[-2]["month"]
        period_a_start = f"{m_prev}-01"
        period_a_end = f"{m_prev}-31"
        period_b_start = f"{m_curr}-01"
        period_b_end = f"{m_curr}-31"

    txns_a = repo.query_transactions(start_date=period_a_start, end_date=period_a_end, category=category, limit=500)
    txns_b = repo.query_transactions(start_date=period_b_start, end_date=period_b_end, category=category, limit=500)

    debit_a = sum(t["debit"] for t in txns_a)
    debit_b = sum(t["debit"] for t in txns_b)
    diff = debit_b - debit_a
    pct = round((diff / debit_a * 100), 1) if debit_a > 0 else 0.0

    return {
        "status": "success",
        "period_baseline": f"{period_a_start} to {period_a_end}",
        "period_target": f"{period_b_start} to {period_b_end}",
        "category_filter": category or "All Categories",
        "baseline_spend": round(debit_a, 2),
        "target_spend": round(debit_b, 2),
        "spend_delta": round(diff, 2),
        "percentage_change": pct,
        "baseline_tx_count": len(txns_a),
        "target_tx_count": len(txns_b),
        "summary": (
            f"Comparison: Spending changed by ₹{round(diff, 2)} ({pct}%) from "
            f"₹{round(debit_a, 2)} ({period_a_start} to {period_a_end}) to ₹{round(debit_b, 2)} ({period_b_start} to {period_b_end})."
        )
    }

