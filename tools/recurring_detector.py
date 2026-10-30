"""
Spendwise AI Tool: recurring_payment_detector
Detects subscription cadences, predictable monthly/weekly debits, and computes annualized exposure.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import numpy as np
from database.repository import Repository

def execute(
    min_occurrences: int = 2,
    repository: Optional[Repository] = None
) -> Dict[str, Any]:
    repo = repository or Repository()
    txns = repo.query_transactions(txn_type="debit", limit=1000)

    if not txns:
        return {"status": "empty", "recurring_count": 0, "recurring_subscriptions": []}

    # Group transactions by merchant and approximate amount
    merchant_groups: Dict[str, List[Dict[str, Any]]] = {}
    for t in txns:
        m = t["merchant"].strip().title()
        merchant_groups.setdefault(m, []).append(t)

    recurring_items = []
    total_monthly_commitment = 0.0

    for merchant, items in merchant_groups.items():
        if len(items) < min_occurrences:
            continue

        # Sort items by date ascending
        valid_items = []
        for it in items:
            try:
                dt = datetime.strptime(it["transaction_date"], "%Y-%m-%d")
                valid_items.append((dt, it))
            except ValueError:
                continue
        valid_items.sort(key=lambda x: x[0])

        if len(valid_items) < min_occurrences:
            continue

        # Check intervals between consecutive transactions
        intervals = []
        amounts = []
        for k in range(len(valid_items) - 1):
            gap = (valid_items[k+1][0] - valid_items[k][0]).days
            intervals.append(gap)
            amounts.append(valid_items[k][1]["debit"])
        amounts.append(valid_items[-1][1]["debit"])

        median_gap = float(np.median(intervals)) if intervals else 0.0
        avg_amt = float(np.mean(amounts))
        amt_std = float(np.std(amounts)) if len(amounts) > 1 else 0.0

        # Consistent amount check (standard deviation < 15% of mean)
        is_consistent_amount = (amt_std / avg_amt < 0.15) or (len(set(amounts)) == 1)

        frequency = "Unknown"
        is_recurring = False
        confidence = 0.70

        # Frequency detection
        if 25 <= median_gap <= 35:
            frequency = "Monthly"
            is_recurring = True
            confidence = 0.95 if is_consistent_amount else 0.80
        elif 6 <= median_gap <= 8:
            frequency = "Weekly"
            is_recurring = True
            confidence = 0.90 if is_consistent_amount else 0.75
        elif 80 <= median_gap <= 100:
            frequency = "Quarterly"
            is_recurring = True
            confidence = 0.85
        elif 350 <= median_gap <= 380:
            frequency = "Annual"
            is_recurring = True
            confidence = 0.90
        elif is_consistent_amount and len(valid_items) >= 3 and median_gap > 0:
            frequency = f"Approx every {int(round(median_gap))} days"
            is_recurring = True
            confidence = 0.75

        if is_recurring:
            # Estimate next date
            last_dt = valid_items[-1][0]
            next_date = (last_dt + timedelta(days=int(round(median_gap)))) if median_gap > 0 else None

            # Calculate monthly & annualized impact
            if frequency == "Monthly":
                monthly_cost = avg_amt
                annual_cost = avg_amt * 12
            elif frequency == "Weekly":
                monthly_cost = avg_amt * 4.33
                annual_cost = avg_amt * 52
            elif frequency == "Quarterly":
                monthly_cost = avg_amt / 3
                annual_cost = avg_amt * 4
            elif frequency == "Annual":
                monthly_cost = avg_amt / 12
                annual_cost = avg_amt
            else:
                monthly_cost = (avg_amt / median_gap) * 30.4 if median_gap > 0 else avg_amt
                annual_cost = monthly_cost * 12

            total_monthly_commitment += monthly_cost

            recurring_items.append({
                "merchant": merchant,
                "category": valid_items[-1][1]["category"],
                "frequency": frequency,
                "average_amount": round(avg_amt, 2),
                "occurrences": len(valid_items),
                "last_charged_date": last_dt.strftime("%Y-%m-%d"),
                "estimated_next_date": next_date.strftime("%Y-%m-%d") if next_date else "N/A",
                "monthly_cost": round(monthly_cost, 2),
                "annualized_cost": round(annual_cost, 2),
                "confidence": confidence,
                "history": [
                    {"date": dt.strftime("%Y-%m-%d"), "amount": it["debit"], "id": it["id"]}
                    for dt, it in valid_items
                ]
            })

    recurring_items.sort(key=lambda x: x["annualized_cost"], reverse=True)

    return {
        "status": "success",
        "recurring_count": len(recurring_items),
        "total_monthly_commitment": round(total_monthly_commitment, 2),
        "total_annualized_commitment": round(total_monthly_commitment * 12, 2),
        "recurring_subscriptions": recurring_items,
        "summary": (
            f"Found {len(recurring_items)} recurring subscriptions & regular payments "
            f"totaling ₹{round(total_monthly_commitment, 2)}/month (₹{round(total_monthly_commitment * 12, 2)}/year)."
        )
    }

