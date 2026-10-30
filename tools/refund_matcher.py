"""
Spendwise AI Tool: refund_matcher
Matches debits with credit reversals, enforces deterministic recovery lifecycle accounting.
"""

from typing import Dict, Any, Optional
from database.repository import Repository
from services.recovery_service import RecoveryService

def execute(
    merchant: Optional[str] = None,
    original_tx_id: Optional[str] = None,
    repository: Optional[Repository] = None
) -> Dict[str, Any]:
    repo = repository or Repository()
    service = RecoveryService(repo)

    # Trigger scan & linking
    service.scan_for_potential_recoveries()
    summary = service.get_summary()
    records = service.get_all()

    # Filter if specific merchant or tx_id requested
    if original_tx_id:
        records = [r for r in records if r["original_transaction_id"] == original_tx_id or r["id"] == original_tx_id]
    elif merchant:
        records = [r for r in records if merchant.lower() in r["merchant"].lower()]

    formatted = []
    for r in records:
        links_data = [
            {
                "credit_date": l["credit_date"],
                "credit_desc": l["credit_desc"],
                "linked_amount": l["linked_amount"],
                "confidence": l["confidence_score"]
            }
            for l in r.get("links", [])
        ]
        formatted.append({
            "recovery_id": r["id"],
            "original_transaction_id": r["original_transaction_id"],
            "original_date": r["original_date"],
            "merchant": r["merchant"],
            "original_payment": r["potential_amount"],
            "potential_recovery": r["potential_amount"],
            "confirmed_recovery": r["confirmed_amount"],
            "unresolved_amount": r["unresolved_amount"],
            "status": r["status"],
            "verified_credit_links": links_data,
            "evidence_notes": r.get("notes") or ""
        })

    return {
        "status": "success",
        "total_cases": len(formatted),
        "total_potential_recovery": summary["total_potential"],
        "total_confirmed_recovery": summary["total_confirmed"],
        "total_unresolved_recovery": summary["total_unresolved"],
        "cases": formatted,
        "recovery_accounting_rules": {
            "verified_recovered_money": "Only linked credits count towards recovered balance.",
            "unresolved_risk": "Potential claims without matching credits remain marked unresolved.",
            "never_fabricate": "Credit reversal must be present in bank statements to be marked confirmed."
        },
        "summary": (
            f"Recovery Tracking: ₹{summary['total_confirmed']} confirmed recovered across "
            f"{summary['total_cases']} tracked refund/dispute case(s), with ₹{summary['total_unresolved']} "
            f"remaining unresolved under investigation."
        )
    }

