"""
Spendwise AI - Recovery Lifecycle Unit Tests
Validates the core novelty of verifiable recovery states:
Potential -> Under Investigation -> Partially Confirmed -> Confirmed -> Unresolved.
"""

import unittest
from database.repository import Repository
from services.recovery_service import RecoveryService

class RecoveryLifecycleTests(unittest.TestCase):
    def setUp(self):
        # Use fresh in-memory database for isolated state testing
        self.repo = Repository(":memory:")
        self.service = RecoveryService(self.repo)

        # Insert a sample debit transaction of 1,000
        txns = [
            {
                "id": "tx_debit_1000",
                "account_id": "acc_primary",
                "transaction_date": "2024-10-10",
                "description": "Shoppers Stop Online Gateway Failed Payment",
                "merchant": "Shoppers Stop",
                "debit": 1000.0,
                "credit": 0.0,
                "currency": "INR",
                "category": "Shopping",
                "reference_id": "REF1000",
                "source_file": "test",
                "source_row": 1,
                "extraction_confidence": 1.0
            }
        ]
        self.repo.insert_transactions(txns)

    def test_initial_potential_state(self):
        records = self.service.scan_for_potential_recoveries()
        self.assertEqual(len(records), 1)
        rec = records[0]
        self.assertEqual(rec["potential_amount"], 1000.0)
        self.assertEqual(rec["confirmed_amount"], 0.0)
        self.assertEqual(rec["unresolved_amount"], 1000.0)
        self.assertEqual(rec["status"], "potential_recovery")

    def test_partial_credit_link(self):
        self.service.scan_for_potential_recoveries()

        # Add partial credit of 300
        credit_txn = [{
            "id": "tx_credit_300",
            "account_id": "acc_primary",
            "transaction_date": "2024-10-12",
            "description": "Shoppers Stop Partial Refund Reversal",
            "merchant": "Shoppers Stop",
            "debit": 0.0,
            "credit": 300.0,
            "currency": "INR",
            "category": "Income",
            "reference_id": "REF300",
            "source_file": "test",
            "source_row": 2,
            "extraction_confidence": 1.0
        }]
        self.repo.insert_transactions(credit_txn)

        # Trigger auto-link
        self.service.match_unlinked_credits()
        records = self.service.get_all()
        rec = records[0]

        # Verify strict accounting: only verified credit counts as recovered money!
        self.assertEqual(rec["potential_amount"], 1000.0)
        self.assertEqual(rec["confirmed_amount"], 300.0)
        self.assertEqual(rec["unresolved_amount"], 700.0)
        self.assertEqual(rec["status"], "partially_confirmed")

    def test_full_credit_link(self):
        self.service.scan_for_potential_recoveries()

        # Add full credit of 1,000
        credit_txn = [{
            "id": "tx_credit_1000",
            "account_id": "acc_primary",
            "transaction_date": "2024-10-14",
            "description": "Shoppers Stop Full Refund Reversal",
            "merchant": "Shoppers Stop",
            "debit": 0.0,
            "credit": 1000.0,
            "currency": "INR",
            "category": "Income",
            "reference_id": "REF1000CR",
            "source_file": "test",
            "source_row": 3,
            "extraction_confidence": 1.0
        }]
        self.repo.insert_transactions(credit_txn)

        self.service.match_unlinked_credits()
        records = self.service.get_all()
        rec = records[0]

        self.assertEqual(rec["potential_amount"], 1000.0)
        self.assertEqual(rec["confirmed_amount"], 1000.0)
        self.assertEqual(rec["unresolved_amount"], 0.0)
        self.assertEqual(rec["status"], "confirmed_recovery")

if __name__ == "__main__":
    unittest.main()

