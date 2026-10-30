"""
Spendwise AI - Ingestion Unit Tests
Tests parsing and normalization for CSV, Excel (.xlsx), and PDF statement formats.
"""

import os
import unittest
from ingestion.csv_parser import parse_csv_file
from ingestion.excel_parser import parse_excel_file
from ingestion.pdf_parser import parse_pdf_file
from ingestion.normalizer import parse_date, extract_merchant, categorize_transaction

class IngestionTests(unittest.TestCase):
    def test_date_parser_variants(self):
        self.assertEqual(parse_date("2024-10-15"), "2024-10-15")
        self.assertEqual(parse_date("15/10/2024"), "2024-10-15")
        self.assertEqual(parse_date("15-10-2024"), "2024-10-15")
        self.assertEqual(parse_date("15 Oct 2024"), "2024-10-15")

    def test_merchant_extraction(self):
        self.assertIn("Swiggy", extract_merchant("UPI/SWIGGY/429810238129/PAYMENT"))
        self.assertIn("Amazon", extract_merchant("POS 4012 AMAZON INDIA"))
        self.assertIn("Netflix", extract_merchant("NETFLIX ENTERTAINMENT SERVICE"))

    def test_categorization_and_corrections(self):
        cat = categorize_transaction("swiggy food delivery", "Swiggy", 450.0, 0.0)
        self.assertEqual(cat, "Food delivery")

        # Test user correction override
        corrections = {"swiggy": "Entertainment"} # user override
        overridden = categorize_transaction("swiggy order", "Swiggy", 450.0, 0.0, user_corrections=corrections)
        self.assertEqual(overridden, "Entertainment")

    def test_csv_ingestion(self):
        csv_path = os.path.join("data", "sample_transactions.csv")
        if os.path.exists(csv_path):
            records, report = parse_csv_file(csv_path)
            self.assertGreater(len(records), 100)
            self.assertEqual(report["rejected_records"], 0)

    def test_excel_ingestion(self):
        xlsx_path = os.path.join("data", "sample_statement.xlsx")
        if os.path.exists(xlsx_path):
            records, report = parse_excel_file(xlsx_path)
            self.assertGreater(len(records), 100)

    def test_pdf_ingestion(self):
        pdf_path = os.path.join("data", "sample_statement.pdf")
        if os.path.exists(pdf_path):
            records, report = parse_pdf_file(pdf_path)
            self.assertGreater(len(records), 10)

if __name__ == "__main__":
    unittest.main()

