"""
Spendwise AI Tool: transaction_search
Enables multi-criteria transaction querying.
"""

from typing import Dict, Any, Optional
from database.repository import Repository

def execute(
    query: Optional[str] = None,
    category: Optional[str] = None,
    merchant: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    txn_type: Optional[str] = None,
    limit: int = 25,
    repository: Optional[Repository] = None
) -> Dict[str, Any]:
    repo = repository or Repository()
    results = repo.query_transactions(
        query_text=query,
        category=category,
        merchant=merchant,
        min_amount=min_amount,
        max_amount=max_amount,
        start_date=start_date,
        end_date=end_date,
        txn_type=txn_type,
        limit=limit
    )

    total_matched = len(results)
    total_debit = sum(r["debit"] for r in results)
    total_credit = sum(r["credit"] for r in results)

    # Return structured observations with exact transaction evidence
    evidence = [
        {
            "id": r["id"],
            "date": r["transaction_date"],
            "merchant": r["merchant"],
            "category": r["category"],
            "debit": r["debit"],
            "credit": r["credit"],
            "description": r["description"],
            "reference": r["reference_id"]
        }
        for r in results[:15]
    ]

    return {
        "status": "success",
        "match_count": total_matched,
        "total_debit_in_matches": round(total_debit, 2),
        "total_credit_in_matches": round(total_credit, 2),
        "transactions": evidence,
        "summary": f"Found {total_matched} transactions matching criteria (Total Debit: ₹{round(total_debit, 2)}, Total Credit: ₹{round(total_credit, 2)})."
    }

