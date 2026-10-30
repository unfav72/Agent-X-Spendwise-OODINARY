"""
Spendwise AI - Tool Unit Tests
Verifies deterministic calculations across all 10 financial auditor tools using an in-memory test fixture.
"""

import unittest
from database.repository import Repository
from services.recovery_service import RecoveryService
from tools.spending_analytics import execute as spending_analytics
from tools.anomaly_detector import execute as anomaly_detector
from tools.duplicate_finder import execute as duplicate_finder
from tools.recurring_detector import execute as recurring_detector
from tools.refund_matcher import execute as refund_matcher
from tools.budget_simulator import execute as budget_simulator
from tools.transaction_comparator import execute as transaction_comparator
from tools.statement_data_validator import execute as statement_data_validator
from tools.report_exporter import execute as report_exporter

class SpendwiseToolsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create dedicated in-memory repository for unit test assertions
        cls.repo = Repository(":memory:")
        txns = [
            # August
            {"id": "t1", "account_id": "acc_primary", "transaction_date": "2024-08-01", "description": "Salary", "merchant": "Techcorp", "debit": 0.0, "credit": 100000.0, "currency": "INR", "category": "Income", "reference_id": "REF01", "source_file": "test", "source_row": 1, "extraction_confidence": 1.0},
            {"id": "t2", "account_id": "acc_primary", "transaction_date": "2024-08-01", "description": "Netflix", "merchant": "Netflix", "debit": 649.0, "credit": 0.0, "currency": "INR", "category": "Subscriptions", "reference_id": "REF02", "source_file": "test", "source_row": 2, "extraction_confidence": 1.0},
            {"id": "t3", "account_id": "acc_primary", "transaction_date": "2024-08-05", "description": "Swiggy Lunch", "merchant": "Swiggy", "debit": 400.0, "credit": 0.0, "currency": "INR", "category": "Food delivery", "reference_id": "REF03", "source_file": "test", "source_row": 3, "extraction_confidence": 1.0},
            # September
            {"id": "t4", "account_id": "acc_primary", "transaction_date": "2024-09-01", "description": "Salary", "merchant": "Techcorp", "debit": 0.0, "credit": 100000.0, "currency": "INR", "category": "Income", "reference_id": "REF04", "source_file": "test", "source_row": 4, "extraction_confidence": 1.0},
            {"id": "t5", "account_id": "acc_primary", "transaction_date": "2024-09-01", "description": "Netflix", "merchant": "Netflix", "debit": 649.0, "credit": 0.0, "currency": "INR", "category": "Subscriptions", "reference_id": "REF05", "source_file": "test", "source_row": 5, "extraction_confidence": 1.0},
            {"id": "t6", "account_id": "acc_primary", "transaction_date": "2024-09-10", "description": "Swiggy Dinner", "merchant": "Swiggy", "debit": 450.0, "credit": 0.0, "currency": "INR", "category": "Food delivery", "reference_id": "REF06", "source_file": "test", "source_row": 6, "extraction_confidence": 1.0},
            # October (Outlier, Duplicate, Recovery Case)
            {"id": "t7", "account_id": "acc_primary", "transaction_date": "2024-10-01", "description": "Salary", "merchant": "Techcorp", "debit": 0.0, "credit": 100000.0, "currency": "INR", "category": "Income", "reference_id": "REF07", "source_file": "test", "source_row": 7, "extraction_confidence": 1.0},
            {"id": "t8", "account_id": "acc_primary", "transaction_date": "2024-10-01", "description": "Netflix", "merchant": "Netflix", "debit": 649.0, "credit": 0.0, "currency": "INR", "category": "Subscriptions", "reference_id": "REF08", "source_file": "test", "source_row": 8, "extraction_confidence": 1.0},
            {"id": "t9", "account_id": "acc_primary", "transaction_date": "2024-10-05", "description": "TV Purchase", "merchant": "Reliance Digital", "debit": 42000.0, "credit": 0.0, "currency": "INR", "category": "Shopping", "reference_id": "REF09", "source_file": "test", "source_row": 9, "extraction_confidence": 1.0},
            {"id": "t10", "account_id": "acc_primary", "transaction_date": "2024-10-12", "description": "Failed Gateway Charge", "merchant": "Shoppers Stop", "debit": 1000.0, "credit": 0.0, "currency": "INR", "category": "Shopping", "reference_id": "REF10", "source_file": "test", "source_row": 10, "extraction_confidence": 1.0},
            {"id": "t11", "account_id": "acc_primary", "transaction_date": "2024-10-15", "description": "Partial Reversal Credit", "merchant": "Shoppers Stop", "debit": 0.0, "credit": 300.0, "currency": "INR", "category": "Income", "reference_id": "REF11CR", "source_file": "test", "source_row": 11, "extraction_confidence": 1.0},
            # Duplicate pair on same day
            {"id": "t12", "account_id": "acc_primary", "transaction_date": "2024-10-18", "description": "Swiggy Order", "merchant": "Swiggy", "debit": 620.0, "credit": 0.0, "currency": "INR", "category": "Food delivery", "reference_id": "SWG99", "source_file": "test", "source_row": 12, "extraction_confidence": 1.0},
            {"id": "t13", "account_id": "acc_primary", "transaction_date": "2024-10-18", "description": "Swiggy Order Dup", "merchant": "Swiggy", "debit": 620.0, "credit": 0.0, "currency": "INR", "category": "Food delivery", "reference_id": "SWG99", "source_file": "test", "source_row": 13, "extraction_confidence": 1.0},
            {"id": "t14", "account_id": "acc_primary", "transaction_date": "2024-10-22", "description": "Swiggy Party", "merchant": "Swiggy", "debit": 1800.0, "credit": 0.0, "currency": "INR", "category": "Food delivery", "reference_id": "SWG100", "source_file": "test", "source_row": 14, "extraction_confidence": 1.0},
        ]
        cls.repo.insert_transactions(txns)
        # Scan recoveries
        RecoveryService(cls.repo).scan_for_potential_recoveries()

    def test_spending_analytics_structure(self):
        res = spending_analytics(repository=self.repo)
        self.assertEqual(res["status"], "success")
        self.assertIn("current_month", res)
        self.assertGreater(res["current_month_expense"], 0)
        self.assertIn("top_increased_categories", res)

    def test_anomaly_detector_catches_spikes(self):
        res = anomaly_detector(threshold_multiplier=1.5, repository=self.repo)
        self.assertEqual(res["status"], "success")
        self.assertGreater(res["anomaly_count"], 0)
        merchants = [a["merchant"] for a in res["anomalies"]]
        self.assertTrue(any("Reliance Digital" in m or "Swiggy" in m for m in merchants))

    def test_duplicate_candidate_finder(self):
        res = duplicate_finder(max_days_gap=2, repository=self.repo)
        self.assertEqual(res["status"], "success")
        self.assertGreater(res["candidate_count"], 0)
        c = res["duplicate_candidates"][0]
        self.assertEqual(c["amount"], 620.0)
        self.assertEqual(c["merchant"], "Swiggy")

    def test_recurring_detector(self):
        res = recurring_detector(min_occurrences=2, repository=self.repo)
        self.assertEqual(res["status"], "success")
        merchants = [r["merchant"] for r in res["recurring_subscriptions"]]
        self.assertTrue(any("Netflix" in m for m in merchants))

    def test_refund_matcher_and_accounting(self):
        res = refund_matcher(repository=self.repo)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["total_confirmed_recovery"], 300.0)
        self.assertEqual(res["total_unresolved_recovery"], 700.0)

    def test_budget_simulator_math(self):
        res = budget_simulator(reductions={"Food delivery": 15.0, "Shopping": 20.0}, repository=self.repo)
        self.assertEqual(res["status"], "success")
        self.assertGreater(res["monthly_hypothetical_savings"], 0)
        self.assertAlmostEqual(res["annualized_hypothetical_savings"], res["monthly_hypothetical_savings"] * 12, places=1)

    def test_statement_validator(self):
        res = statement_data_validator(repository=self.repo)
        self.assertEqual(res["status"], "success")
        self.assertGreaterEqual(res["statement_health_score"], 80)

    def test_report_exporter(self):
        res = report_exporter(repository=self.repo)
        self.assertEqual(res["status"], "success")
        self.assertIn("audit_bundle", res)

if __name__ == "__main__":
    unittest.main()
