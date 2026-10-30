"""
Spendwise AI Tool: anomaly_detector
Scans transactions for statistical spikes, category velocity anomalies, and unusual frequency.
"""

from typing import Dict, Any, List, Optional
import numpy as np
from database.repository import Repository

def execute(
    threshold_multiplier: float = 2.5,
    repository: Optional[Repository] = None
) -> Dict[str, Any]:
    repo = repository or Repository()
    txns = repo.query_transactions(limit=1000)
    
    if not txns:
        return {"status": "empty", "message": "No transactions available for anomaly detection.", "anomalies": []}

    debits = [t for t in txns if t["debit"] > 0]
    if len(debits) < 5:
        return {"status": "insufficient_data", "message": "At least 5 debit transactions required for statistical anomaly detection.", "anomalies": []}

    # Group by category to compute baselines
    cat_amounts: Dict[str, List[float]] = {}
    for t in debits:
        cat = t["category"]
        cat_amounts.setdefault(cat, []).append(t["debit"])

    cat_stats = {}
    for cat, amts in cat_amounts.items():
        mean = float(np.mean(amts))
        std = float(np.std(amts)) if len(amts) > 1 else 0.0
        cat_stats[cat] = {"mean": mean, "std": std}

    anomalies = []

    # 1. High value / spike anomaly
    for t in debits:
        cat = t["category"]
        stats = cat_stats[cat]
        mean = stats["mean"]
        std = stats["std"]
        amt = t["debit"]

        is_spike = False
        reason = ""
        severity = "medium"

        if std > 0 and amt > (mean + threshold_multiplier * std) and amt >= 1500.0:
            is_spike = True
            delta = amt - mean
            reason = f"Transaction amount ₹{amt} is significantly higher than category '{cat}' mean (₹{round(mean, 2)} + {threshold_multiplier}σ)."
            severity = "high" if amt > (mean + 3.5 * std) else "medium"
        elif amt >= 15000.0 and amt > 3 * mean:
            is_spike = True
            delta = amt - mean
            reason = f"High-value payment of ₹{amt} exceeds 3x normal category benchmark of ₹{round(mean, 2)}."
            severity = "critical"

        if is_spike:
            anomalies.append({
                "id": f"anom_{t['id']}",
                "transaction_id": t["id"],
                "transaction_date": t["transaction_date"],
                "merchant": t["merchant"],
                "category": cat,
                "amount": t["debit"],
                "anomaly_type": "spending_spike",
                "severity": severity,
                "reason": reason,
                "historical_baseline": round(mean, 2),
                "delta_amount": round(amt - mean, 2),
                "confidence": 0.92,
                "recommended_action": "Verify invoice and confirm whether this was an intended one-time purchase or an erroneous bill."
            })

    # 2. Check for same-day rapid frequency (velocity anomaly)
    date_merchant_counts: Dict[str, List[Dict[str, Any]]] = {}
    for t in debits:
        key = f"{t['transaction_date']}_{t['merchant'].lower()}"
        date_merchant_counts.setdefault(key, []).append(t)

    for key, items in date_merchant_counts.items():
        if len(items) >= 3:
            total_freq_spend = sum(x["debit"] for x in items)
            anomalies.append({
                "id": f"anom_vel_{items[0]['id']}",
                "transaction_id": items[0]["id"],
                "transaction_date": items[0]["transaction_date"],
                "merchant": items[0]["merchant"],
                "category": items[0]["category"],
                "amount": items[0]["debit"],
                "anomaly_type": "high_frequency_velocity",
                "severity": "high",
                "reason": f"Unusual burst of {len(items)} transactions to '{items[0]['merchant']}' within a single day totaling ₹{round(total_freq_spend, 2)}.",
                "historical_baseline": 1.0,
                "delta_amount": round(total_freq_spend, 2),
                "confidence": 0.88,
                "recommended_action": "Inspect merchant statements to rule out repeated automated charges or unapplied coupons."
            })

    # Save to database
    repo.save_anomalies(anomalies)

    return {
        "status": "success",
        "anomaly_count": len(anomalies),
        "anomalies": anomalies,
        "summary": f"Detected {len(anomalies)} statistical spending anomalies and velocity alerts."
    }

