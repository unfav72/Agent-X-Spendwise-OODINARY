"""
Spendwise AI Tool: spending_analytics
Provides deterministic financial aggregates, category velocity, and month-over-month comparisons.
"""

from typing import Dict, Any, Optional
from database.repository import Repository

def execute(
    target_month: Optional[str] = None, # e.g. '2024-10'
    repository: Optional[Repository] = None
) -> Dict[str, Any]:
    repo = repository or Repository()
    overview = repo.get_spending_overview()
    monthly = overview.get("monthly_trend", [])

    if not monthly:
        return {
            "status": "empty",
            "message": "No transaction records found in database.",
            "total_expense": 0.0,
            "total_income": 0.0
        }

    # If target_month not specified, use latest available month
    months_available = [m["month"] for m in monthly]
    curr_month = target_month if (target_month and target_month in months_available) else months_available[-1]
    
    # Identify previous month for comparison
    curr_idx = months_available.index(curr_month)
    prev_month = months_available[curr_idx - 1] if curr_idx > 0 else None

    # Get category spending for current month
    all_txns = repo.query_transactions(limit=1000)
    curr_txns = [t for t in all_txns if t["transaction_date"].startswith(curr_month)]
    prev_txns = [t for t in all_txns if prev_month and t["transaction_date"].startswith(prev_month)]

    curr_cat_spend = {}
    for t in curr_txns:
        if t["debit"] > 0:
            cat = t["category"]
            curr_cat_spend[cat] = curr_cat_spend.get(cat, 0.0) + t["debit"]

    prev_cat_spend = {}
    for t in prev_txns:
        if t["debit"] > 0:
            cat = t["category"]
            prev_cat_spend[cat] = prev_cat_spend.get(cat, 0.0) + t["debit"]

    # Category comparisons and deltas
    category_deltas = []
    all_cats = set(curr_cat_spend.keys()).union(set(prev_cat_spend.keys()))
    for cat in all_cats:
        c_amt = curr_cat_spend.get(cat, 0.0)
        p_amt = prev_cat_spend.get(cat, 0.0)
        diff = c_amt - p_amt
        pct_change = round((diff / p_amt * 100), 1) if p_amt > 0 else (100.0 if c_amt > 0 else 0.0)
        category_deltas.append({
            "category": cat,
            "current_month_spent": round(c_amt, 2),
            "prev_month_spent": round(p_amt, 2),
            "change_amount": round(diff, 2),
            "percentage_change": pct_change
        })

    category_deltas.sort(key=lambda x: x["change_amount"], reverse=True)

    curr_total_debit = sum(curr_cat_spend.values())
    prev_total_debit = sum(prev_cat_spend.values())
    net_diff = curr_total_debit - prev_total_debit
    overall_pct = round((net_diff / prev_total_debit * 100), 1) if prev_total_debit > 0 else 0.0

    return {
        "status": "success",
        "current_month": curr_month,
        "previous_month": prev_month,
        "current_month_expense": round(curr_total_debit, 2),
        "prev_month_expense": round(prev_total_debit, 2),
        "expense_change_amount": round(net_diff, 2),
        "expense_percentage_change": overall_pct,
        "top_increased_categories": category_deltas[:5],
        "top_overall_categories": sorted(
            [{"category": k, "amount": round(v, 2)} for k, v in curr_cat_spend.items()],
            key=lambda x: x["amount"],
            reverse=True
        )[:5],
        "total_lifetime_income": overview["total_income"],
        "total_lifetime_expense": overview["total_expense"],
        "net_balance": overview["net_balance"],
        "summary": (
            f"Spending in {curr_month} was ₹{round(curr_total_debit, 2)} "
            f"({'increased by ₹' + str(round(net_diff, 2)) + ' (' + str(overall_pct) + '%)' if net_diff > 0 else 'decreased by ₹' + str(abs(round(net_diff, 2)))}) "
            f"compared to {prev_month or 'prior period'}."
        )
    }

