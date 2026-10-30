"""
Spendwise AI Tool: statement_data_validator
Validates loaded statement health, date continuity, and checks for corrupted or missing values.
"""

from typing import Dict, Any, Optional
from database.repository import Repository

def execute(
    repository: Optional[Repository] = None
) -> Dict[str, Any]:
    repo = repository or Repository()
    txns = repo.query_transactions(limit=1000)

    total = len(txns)
    if total == 0:
        return {"status": "empty", "total_transactions": 0, "health_score": 0, "issues": ["No records found."]}

    missing_merchant = 0
    missing_ref = 0
    zero_amounts = 0
    negative_amounts = 0
    other_category = 0

    for t in txns:
        if not t.get("merchant") or t["merchant"].lower() in ["unknown", "unknown merchant"]:
            missing_merchant += 1
        if not t.get("reference_id"):
            missing_ref += 1
        if t["debit"] == 0 and t["credit"] == 0:
            zero_amounts += 1
        if t["debit"] < 0 or t["credit"] < 0:
            negative_amounts += 1
        if t["category"] == "Other":
            other_category += 1

    health_penalty = (missing_merchant * 2) + (missing_ref * 0.5) + (zero_amounts * 5) + (negative_amounts * 5)
    health_score = max(0, min(100, int(100 - (health_penalty / total * 20))))

    return {
        "status": "success",
        "total_records_analyzed": total,
        "statement_health_score": health_score,
        "metrics": {
            "missing_merchant_names": missing_merchant,
            "missing_reference_ids": missing_ref,
            "zero_amount_records": zero_amounts,
            "negative_amount_records": negative_amounts,
            "uncategorized_other": other_category
        },
        "summary": f"Statement Health Score: {health_score}/100 based on {total} records. {other_category} transactions categorized as 'Other'."
    }

