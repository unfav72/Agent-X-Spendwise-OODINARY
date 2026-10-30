"""
Spendwise AI - Recovery Service
Manages the audit-grade recovery lifecycle: potential -> under investigation -> verified credits -> unresolved balance.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from database.repository import Repository

class RecoveryService:
    def __init__(self, repository: Optional[Repository] = None):
        self.repo = repository or Repository()

    def scan_for_potential_recoveries(self) -> List[Dict[str, Any]]:
        """
        Scans transactions for potential refund candidates:
        - Debits with keywords 'failed', 'declined', 'cancelled', 'disputed', 'double'
        - Explicitly flagged anomalous transactions
        - Repeated payments where one might be refundable
        """
        existing = {r["original_transaction_id"]: r for r in self.repo.get_recovery_records()}
        candidates = []

        # Find debits with failed/reversed indicators or user-reported disputes
        all_txns = self.repo.query_transactions(limit=500)
        for t in all_txns:
            if t["debit"] <= 0:
                continue
            
            t_id = t["id"]
            if t_id in existing:
                continue

            desc_lower = t["description"].lower()
            reasons = []
            if any(w in desc_lower for w in ["failed", "reversal pending", "cancelled", "declined", "dispute"]):
                reasons.append("Transaction description indicates failed or disputed charge")

            # Check if there is an anomaly record for this transaction
            anomalies = self.repo.get_anomalies()
            for a in anomalies:
                if a["transaction_id"] == t_id and a["anomaly_type"] in ["duplicate_candidate", "spike"]:
                    reasons.append(f"Flagged anomaly: {a['reason']}")

            if reasons:
                rec_id = f"rec_{t_id}"
                record = {
                    "id": rec_id,
                    "original_transaction_id": t_id,
                    "potential_amount": float(t["debit"]),
                    "confirmed_amount": 0.0,
                    "unresolved_amount": float(t["debit"]),
                    "status": "potential_recovery",
                    "merchant": t["merchant"],
                    "notes": "; ".join(reasons)
                }
                self.repo.save_recovery_record(record)
                candidates.append(record)

        # Auto-match with credits
        self.match_unlinked_credits()
        return self.repo.get_recovery_records()

    def match_unlinked_credits(self):
        """
        Finds credits that correspond to active recovery records:
        - Same or similar merchant
        - Credit date on or after debit date
        - Credit amount <= unresolved amount
        """
        records = self.repo.get_recovery_records()
        credits = self.repo.query_transactions(txn_type="credit", limit=200)

        for rec in records:
            if rec["unresolved_amount"] <= 0:
                continue

            # Check existing linked credit IDs
            existing_linked_ids = {link["credit_transaction_id"] for link in rec.get("links", [])}
            m_rec = rec["merchant"].lower()

            for c in credits:
                if c["id"] in existing_linked_ids:
                    continue

                m_c = c["merchant"].lower()
                desc_c = c["description"].lower()

                # Merchant match or description match
                merchant_match = (m_rec in m_c or m_c in m_rec or m_rec in desc_c)
                is_credit = c["credit"] > 0

                # Date comparison
                try:
                    c_date = datetime.strptime(c["transaction_date"], "%Y-%m-%d")
                    orig_date = datetime.strptime(rec["original_date"], "%Y-%m-%d")
                    is_after = c_date >= orig_date
                except Exception:
                    is_after = True

                if is_credit and merchant_match and is_after:
                    amt_to_link = min(float(c["credit"]), float(rec["unresolved_amount"]))
                    if amt_to_link > 0:
                        self.repo.add_recovery_link(
                            recovery_id=rec["id"],
                            credit_txn_id=c["id"],
                            linked_amount=amt_to_link,
                            confidence_score=0.95 if m_rec == m_c else 0.80,
                            notes=f"Auto-linked credit from {c['merchant']} on {c['transaction_date']}"
                        )
                        break # Link one at a time

    def register_manual_recovery_claim(self, original_tx_id: str, notes: str = "User initiated refund inquiry") -> Optional[Dict[str, Any]]:
        """Allow user to explicitly register a debit for recovery investigation."""
        txns = self.repo.query_transactions()
        target = next((t for t in txns if t["id"] == original_tx_id), None)
        if not target or target["debit"] <= 0:
            return None

        rec_id = f"rec_{original_tx_id}"
        record = {
            "id": rec_id,
            "original_transaction_id": original_tx_id,
            "potential_amount": float(target["debit"]),
            "confirmed_amount": 0.0,
            "unresolved_amount": float(target["debit"]),
            "status": "refund_requested",
            "merchant": target["merchant"],
            "notes": notes
        }
        self.repo.save_recovery_record(record)
        self.match_unlinked_credits()
        return record

    def get_recovery_timeline(self, recovery_id: str) -> Optional[Dict[str, Any]]:
        records = self.repo.get_recovery_records()
        target = next((r for r in records if r["id"] == recovery_id), None)
        if not target:
            return None

        events = []
        events.append({
            "stage": "Original Payment",
            "date": target["original_date"],
            "amount": target["potential_amount"],
            "details": f"Payment to {target['merchant']}: {target['original_description']}"
        })
        events.append({
            "stage": "Recovery Case Created",
            "date": target["created_at"][:10],
            "status": target["status"],
            "details": target.get("notes") or "Investigation initiated"
        })

        for link in target.get("links", []):
            events.append({
                "stage": "Verified Credit Linked",
                "date": link["credit_date"],
                "amount": link["linked_amount"],
                "confidence": link["confidence_score"],
                "details": f"Credit received: {link['credit_desc']} (Ref: {link.get('credit_ref') or 'N/A'})"
            })

        summary = {
            "record": target,
            "events": events,
            "potential_recovery": target["potential_amount"],
            "confirmed_recovery": target["confirmed_amount"],
            "unresolved_amount": target["unresolved_amount"],
            "is_fully_recovered": target["unresolved_amount"] == 0.0 and target["confirmed_amount"] > 0.0
        }
        return summary

    def get_summary(self) -> Dict[str, Any]:
        return self.repo.get_recovery_summary()

    def get_all(self) -> List[Dict[str, Any]]:
        return self.repo.get_recovery_records()

