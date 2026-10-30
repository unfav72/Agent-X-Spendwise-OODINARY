"""
Spendwise AI - PDF Statement Parser
Extracts transaction rows from bank & UPI statement PDFs using pypdf.
"""

import os
import re
from typing import List, Dict, Any, Tuple
from pypdf import PdfReader
from .normalizer import normalize_row
from .validator import StatementValidator

# Regex matching typical statement transaction line:
# e.g., 2024-10-15 Swiggy Food Order 450.00 0.00 123456789
# or 15/10/2024 UPI/ZOMATO/12345 520.00
LINE_REGEX = re.compile(
    r"^(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4})\s+"
    r"(.+?)\s+"
    r"([0-9,]+\.[0-9]{2})\s*"
    r"([0-9,]+\.[0-9]{2})?\s*"
    r"([A-Za-z0-9_-]{8,})?$"
)

def parse_pdf_file(file_path: str, user_corrections: Dict[str, str] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    filename = os.path.basename(file_path)
    reader = PdfReader(file_path)
    raw_rows = []
    row_counter = 1

    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        lines = [l.strip() for l in text.splitlines() if l.strip()]

        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check if this line is a date (cell-by-cell vertical table extraction)
            date_match = re.match(r"^(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4})$", line)
            if date_match and i + 3 < len(lines):
                # Try reading vertical block: Date, Description, Debit, Credit, (optional Reference)
                d_str = date_match.group(1)
                desc = lines[i+1]
                amt1_str = lines[i+2].replace(",", "")
                amt2_str = lines[i+3].replace(",", "")
                
                try:
                    val1 = float(amt1_str)
                    val2 = float(amt2_str)
                    ref = None
                    advance = 4
                    if i + 4 < len(lines) and not re.match(r"^(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4})$", lines[i+4]):
                        ref = lines[i+4]
                        advance = 5

                    row_dict = {
                        "date": d_str,
                        "description": desc,
                        "debit": val1,
                        "credit": val2,
                        "reference": ref
                    }
                    normalized = normalize_row(row_dict, source_file=f"{filename}:p{page_num}", row_index=row_counter, user_corrections=user_corrections)
                    if normalized:
                        raw_rows.append(normalized)
                        row_counter += 1
                    i += advance
                    continue
                except ValueError:
                    pass

            # Horizontal single-line match
            match = LINE_REGEX.match(line)
            if match:
                date_str = match.group(1)
                desc = match.group(2).strip()
                amt1_str = match.group(3).replace(",", "")
                amt2_str = match.group(4).replace(",", "") if match.group(4) else None
                ref = match.group(5)

                if amt2_str:
                    debit = float(amt1_str)
                    credit = float(amt2_str)
                else:
                    amt1 = float(amt1_str)
                    if any(w in desc.lower() for w in ["salary", "credit", "refund", "reversal"]):
                        debit = 0.0
                        credit = amt1
                    else:
                        debit = amt1
                        credit = 0.0

                row_dict = {
                    "date": date_str,
                    "description": desc,
                    "debit": debit,
                    "credit": credit,
                    "reference": ref
                }
                normalized = normalize_row(row_dict, source_file=f"{filename}:p{page_num}", row_index=row_counter, user_corrections=user_corrections)
                if normalized:
                    raw_rows.append(normalized)
                    row_counter += 1
            i += 1

    return StatementValidator.validate_transactions(raw_rows)
