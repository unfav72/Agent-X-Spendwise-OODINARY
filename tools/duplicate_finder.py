"""
Spendwise AI Tool: duplicate_candidate_finder
Identifies potential duplicate charges based on amount equivalence, merchant similarity, and temporal proximity.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from database.repository import Repository

def execute(
    max_days_gap: int = 3,
    repository: Optional[Repository] = None
) -> Dict[str, Any]:
    repo = repository or Repository()
    txns = repo.query_transactions(txn_type="debit", limit=1000)

    if len(txns) < 2:
        return {"status": "insufficient_data", "candidate_count": 0, "duplicate_candidates": []}

    candidates = []
    seen_pairs = set()

    for i in range(len(txns)):
        t1 = txns[i]
        try:
            d1 = datetime.strptime(t1["transaction_date"], "%Y-%m-%d")
        except ValueError:
            continue

        for j in range(i + 1, len(txns)):
            t2 = txns[j]
            try:
                d2 = datetime.strptime(t2["transaction_date"], "%Y-%m-%d")
            except ValueError:
                continue

            days_diff = abs((d1 - d2).days)
            if days_diff > max_days_gap:
                continue

            # Amount check
            amt1 = t1["debit"]
            amt2 = t2["debit"]
            if amt1 <= 0 or amt2 <= 0:
                continue

            # Exact amount match
            same_amount = (abs(amt1 - amt2) < 0.01)

            # Merchant / description similarity
            m1 = t1["merchant"].strip().lower()
            m2 = t2["merchant"].strip().lower()
            same_merchant = (m1 == m2 or m1 in m2 or m2 in m1)

            if same_amount and same_merchant:
                pair_key = tuple(sorted([t1["id"], t2["id"]]))
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                # Confidence calculation
                confidence = 0.95 if days_diff == 0 else (0.85 if days_diff == 1 else 0.70)
                
                # Check reference ids
                ref1 = t1.get("reference_id")
                ref2 = t2.get("reference_id")
                if ref1 and ref2 and ref1 == ref2:
                    confidence = 0.99
                    reason = f"Identical amount (₹{amt1}), same merchant '{t1['merchant']}', and identical reference ID '{ref1}' within {days_diff} day(s)."
                else:
                    reason = f"Identical amount (₹{amt1}) and same merchant '{t1['merchant']}' billed twice within {days_diff} day(s)."

                candidate = {
                    "pair_id": f"dup_{t1['id']}_{t2['id']}",
                    "merchant": t1["merchant"],
                    "amount": amt1,
                    "days_apart": days_diff,
                    "confidence": confidence,
                    "status": "candidate_requires_review",
                    "reason": reason,
                    "primary_transaction": {
                        "id": t1["id"],
                        "date": t1["transaction_date"],
                        "description": t1["description"],
                        "reference": t1["reference_id"]
                    },
                    "duplicate_transaction": {
                        "id": t2["id"],
                        "date": t2["transaction_date"],
                        "description": t2["description"],
                        "reference": t2["reference_id"]
                    },
                    "recommended_action": "Check bank statement or merchant order history to verify if two independent orders were placed or if one was an erroneous double charge."
                }
                candidates.append(candidate)

    return {
        "status": "success",
        "candidate_count": len(candidates),
        "duplicate_candidates": candidates,
        "summary": f"Discovered {len(candidates)} potential duplicate charge candidates for review."
    }

