"""
Spendwise AI - Excel Statement Parser
Extracts transaction rows from .xlsx / .xls files using openpyxl.
"""

import os
from typing import List, Dict, Any, Tuple
import openpyxl
from .normalizer import normalize_row
from .validator import StatementValidator

def parse_excel_file(file_path: str, user_corrections: Dict[str, str] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    filename = os.path.basename(file_path)
    wb = openpyxl.load_workbook(file_path, data_only=True)
    sheet = wb.active

    rows = list(sheet.iter_rows(values_only=True))
    if not rows:
        return [], {"error": "Empty Excel sheet"}

    # Find the header row (the first row with at least 3 non-empty cells)
    header_idx = -1
    headers = []
    for idx, row in enumerate(rows):
        non_empty = [str(c).strip() for c in row if c is not None and str(c).strip()]
        if len(non_empty) >= 3:
            headers = [str(c).strip() if c is not None else f"col_{i}" for i, c in enumerate(row)]
            header_idx = idx
            break

    if header_idx == -1:
        return [], {"error": "Could not identify header row in Excel file"}

    raw_rows = []
    for row_idx, row in enumerate(rows[header_idx + 1:], start=header_idx + 2):
        row_dict = {}
        for h, val in zip(headers, row):
            if h:
                row_dict[h] = val
        normalized = normalize_row(row_dict, source_file=filename, row_index=row_idx, user_corrections=user_corrections)
        if normalized:
            raw_rows.append(normalized)

    return StatementValidator.validate_transactions(raw_rows)

