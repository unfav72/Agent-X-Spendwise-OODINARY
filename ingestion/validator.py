"""
Spendwise AI - Ingestion Data Validator
Performs deterministic integrity checks on parsed statement records.
"""

from typing import List, Dict, Any, Tuple

class StatementValidator:
    @staticmethod
    def validate_transactions(records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Validates records, flags anomalies, and returns (clean_records, report).
        """
        valid_records = []
        errors = []
        warnings = []
        seen_refs = set()
        duplicate_ref_count = 0
        zero_amount_count = 0
        missing_date_count = 0

        for idx, rec in enumerate(records):
            row_id = rec.get("id", f"row_{idx}")
            date = rec.get("transaction_date")
            debit = float(rec.get("debit", 0.0) or 0.0)
            credit = float(rec.get("credit", 0.0) or 0.0)
            ref = rec.get("reference_id")

            if not date:
                missing_date_count += 1
                errors.append(f"Row {idx}: Missing transaction date.")
                continue

            if debit < 0 or credit < 0:
                warnings.append(f"Row {idx} ({row_id}): Negative debit/credit detected and sanitized.")
                rec["debit"] = abs(debit)
                rec["credit"] = abs(credit)

            if rec["debit"] == 0.0 and rec["credit"] == 0.0:
                zero_amount_count += 1
                errors.append(f"Row {idx}: Zero debit and credit amount.")
                continue

            if ref:
                if ref in seen_refs:
                    duplicate_ref_count += 1
                    warnings.append(f"Row {idx}: Duplicate reference ID '{ref}' observed.")
                else:
                    seen_refs.add(ref)

            valid_records.append(rec)

        report = {
            "total_submitted": len(records),
            "valid_records": len(valid_records),
            "rejected_records": len(records) - len(valid_records),
            "warnings_count": len(warnings),
            "duplicate_ref_count": duplicate_ref_count,
            "zero_amount_count": zero_amount_count,
            "missing_date_count": missing_date_count,
            "warnings": warnings[:15],
            "errors": errors[:15]
        }

        return valid_records, report

