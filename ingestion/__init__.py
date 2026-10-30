import os
from typing import List, Dict, Any, Tuple
from .csv_parser import parse_csv_file
from .excel_parser import parse_excel_file
from .pdf_parser import parse_pdf_file
from .normalizer import CATEGORIES, extract_merchant, categorize_transaction
from .validator import StatementValidator

def ingest_file(file_path: str, user_corrections: Dict[str, str] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Automatically detect format by extension and ingest transactions."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".csv":
        return parse_csv_file(file_path, user_corrections=user_corrections)
    elif ext in [".xlsx", ".xls"]:
        return parse_excel_file(file_path, user_corrections=user_corrections)
    elif ext == ".pdf":
        return parse_pdf_file(file_path, user_corrections=user_corrections)
    else:
        raise ValueError(f"Unsupported file format: {ext}. Supported formats: .csv, .xlsx, .xls, .pdf")

__all__ = [
    "ingest_file",
    "parse_csv_file",
    "parse_excel_file",
    "parse_pdf_file",
    "CATEGORIES",
    "extract_merchant",
    "categorize_transaction",
    "StatementValidator"
]

