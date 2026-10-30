"""
Spendwise AI - User Dataset Ingestion Utility
Loads data/Transactions.csv efficiently in chunks into spendwise.db.
"""

import os
import sys
import time
import csv

# Ensure root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.repository import Repository
from ingestion.normalizer import normalize_row
from services.recovery_service import RecoveryService
from tools.anomaly_detector import execute as run_anomalies

def load_user_dataset(limit_rows: int = None, chunk_size: int = 10000):
    csv_path = os.path.join("data", "Transactions.csv")
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    repo = Repository()
    repo.reset_all()
    print("Database reset. Ingesting from data/Transactions.csv...")

    t0 = time.time()
    total_inserted = 0
    buffer = []

    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            norm = normalize_row(row, source_file="Transactions.csv", row_index=i)
            if norm:
                buffer.append(norm)

            if len(buffer) >= chunk_size:
                repo.insert_transactions(buffer)
                total_inserted += len(buffer)
                print(f"  Inserted {total_inserted:,} records... ({time.time() - t0:.1f}s)")
                buffer = []

            if limit_rows and i >= limit_rows:
                break

        if buffer:
            repo.insert_transactions(buffer)
            total_inserted += len(buffer)

    t1 = time.time()
    print(f"\n[SUCCESS] Loaded {total_inserted:,} transactions into spendwise.db in {t1 - t0:.1f} seconds!")

    # Scan for potential recoveries and anomalies
    print("Scanning for failed deductions and potential recoveries...")
    rec_service = RecoveryService(repo)
    rec_records = rec_service.scan_for_potential_recoveries()
    print(f"Identified {len(rec_records)} recovery / dispute cases.")

    print("Running initial anomaly detection baseline...")
    anom_res = run_anomalies(repository=repo)
    print(f"Flagged {anom_res.get('anomaly_count', 0)} spending anomalies.")

if __name__ == "__main__":
    # Ingest up to 50,000 transactions for optimal performance or all if needed
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 50000
    load_user_dataset(limit_rows=limit)

