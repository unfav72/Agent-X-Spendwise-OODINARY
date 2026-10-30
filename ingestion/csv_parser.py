"""
Spendwise AI - CSV Statement Parser
Extracts transaction rows from CSV statements with robust delimiter and encoding handling.
"""

import os
import csv
from typing import List, Dict, Any, Tuple
from .normalizer import normalize_row
from .validator import StatementValidator

def parse_csv_file(file_path: str, user_corrections: Dict[str, str] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    filename = os.path.basename(file_path)
    raw_rows = []

    # Try utf-8, then latin-1 fallback
    encodings = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc) as f:
                # Read sample to detect dialect
                sample = f.read(4096)
                f.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample)
                    delimiter = dialect.delimiter
                except Exception:
                    delimiter = ","
                
                reader = csv.DictReader(f, delimiter=delimiter)
                for row_idx, row in enumerate(reader, start=1):
                    normalized = normalize_row(row, source_file=filename, row_index=row_idx, user_corrections=user_corrections)
                    if normalized:
                        raw_rows.append(normalized)
            break
        except UnicodeDecodeError:
            continue

    return StatementValidator.validate_transactions(raw_rows)

