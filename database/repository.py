"""
Spendwise AI - Database Repository Layer
Provides reliable SQLite persistence, migrations, and transactional querying.
"""

import os
import sqlite3
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

DEFAULT_DB_FILENAME = "spendwise.db"

def get_db_path() -> str:
    """Resolve database path respecting AGENTX_DATA_DIR if provided."""
    data_dir = os.environ.get("AGENTX_DATA_DIR", "").strip()
    if data_dir:
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, DEFAULT_DB_FILENAME)
    # Default to current directory
    return os.path.abspath(DEFAULT_DB_FILENAME)

class Repository:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_db_path()
        self._mem_conn: Optional[sqlite3.Connection] = None
        if self.db_path == ":memory:":
            self._mem_conn = sqlite3.connect(":memory:")
            self._mem_conn.row_factory = sqlite3.Row
            self._mem_conn.execute("PRAGMA foreign_keys = ON;")
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        if self._mem_conn is not None:
            return self._mem_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self):
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        if not os.path.exists(schema_path):
            raise FileNotFoundError(f"Schema file not found at {schema_path}")
        
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        
        with self.get_connection() as conn:
            conn.executescript(schema_sql)
            # Default account if none exists
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM accounts")
            if cur.fetchone()[0] == 0:
                cur.execute(
                    "INSERT INTO accounts (id, name, account_type, institution, currency) "
                    "VALUES ('acc_primary', 'Primary Account', 'checking', 'HDFC Bank', 'INR')"
                )
            conn.commit()

    # --- Transaction Operations ---

    def insert_transactions(self, transactions: List[Dict[str, Any]]) -> int:
        if not transactions:
            return 0
        
        insert_sql = """
            INSERT OR REPLACE INTO transactions (
                id, account_id, transaction_date, description, merchant,
                debit, credit, currency, category, reference_id,
                source_file, source_row, extraction_confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        rows = []
        for t in transactions:
            rows.append((
                t["id"],
                t.get("account_id", "acc_primary"),
                t["transaction_date"],
                t["description"],
                t.get("merchant", "Unknown"),
                float(t.get("debit", 0.0) or 0.0),
                float(t.get("credit", 0.0) or 0.0),
                t.get("currency", "INR"),
                t.get("category", "Other"),
                t.get("reference_id"),
                t.get("source_file"),
                t.get("source_row"),
                float(t.get("extraction_confidence", 1.0))
            ))

        with self.get_connection() as conn:
            conn.executemany(insert_sql, rows)
            conn.commit()
        return len(rows)

    def query_transactions(
        self,
        query_text: Optional[str] = None,
        category: Optional[str] = None,
        merchant: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        txn_type: Optional[str] = None, # 'debit', 'credit'
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM transactions WHERE 1=1"
        params = []

        if query_text:
            sql += " AND (description LIKE ? OR merchant LIKE ? OR reference_id LIKE ?)"
            term = f"%{query_text}%"
            params.extend([term, term, term])
        
        if category and category.lower() != "all":
            sql += " AND LOWER(category) = LOWER(?)"
            params.append(category)

        if merchant:
            sql += " AND LOWER(merchant) LIKE LOWER(?)"
            params.append(f"%{merchant}%")

        if min_amount is not None:
            if txn_type == "credit":
                sql += " AND credit >= ?"
            else:
                sql += " AND (debit >= ? OR credit >= ?)"
                params.append(min_amount)
            params.append(min_amount)

        if max_amount is not None:
            if txn_type == "credit":
                sql += " AND credit <= ?"
            else:
                sql += " AND (debit <= ? AND credit <= ?)"
                params.append(max_amount)
            params.append(max_amount)

        if start_date:
            sql += " AND transaction_date >= ?"
            params.append(start_date)

        if end_date:
            sql += " AND transaction_date <= ?"
            params.append(end_date)

        if txn_type == "debit":
            sql += " AND debit > 0"
        elif txn_type == "credit":
            sql += " AND credit > 0"

        sql += " ORDER BY transaction_date DESC, id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]

    def count_transactions(self) -> int:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM transactions")
            return cur.fetchone()[0]

    def update_transaction_category(self, transaction_id: str, new_category: str) -> bool:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE transactions SET category = ? WHERE id = ?",
                (new_category, transaction_id)
            )
            # Fetch merchant to store user correction for future learning
            cur.execute("SELECT merchant FROM transactions WHERE id = ?", (transaction_id,))
            row = cur.fetchone()
            if row and row["merchant"]:
                cur.execute(
                    "INSERT OR REPLACE INTO user_category_corrections (keyword_or_merchant, corrected_category) "
                    "VALUES (?, ?)",
                    (row["merchant"].strip().lower(), new_category)
                )
            conn.commit()
            return cur.rowcount > 0

    def get_user_category_corrections(self) -> Dict[str, str]:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT keyword_or_merchant, corrected_category FROM user_category_corrections")
            return {row["keyword_or_merchant"]: row["corrected_category"] for row in cur.fetchall()}

    # --- Financial Aggregations & Analytics ---

    def get_spending_overview(self) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT SUM(debit) as total_debit, SUM(credit) as total_credit, COUNT(*) as count FROM transactions")
            summary = cur.fetchone()
            total_debit = summary["total_debit"] or 0.0
            total_credit = summary["total_credit"] or 0.0
            count = summary["count"] or 0

            # Net Balance calculated within scope of loaded records
            net_balance = total_credit - total_debit

            # Date range
            cur.execute("SELECT MIN(transaction_date) as start_date, MAX(transaction_date) as end_date FROM transactions")
            dates = cur.fetchone()

            # Top categories
            cur.execute("""
                SELECT category, SUM(debit) as total_spent, COUNT(*) as tx_count
                FROM transactions
                WHERE debit > 0
                GROUP BY category
                ORDER BY total_spent DESC
            """)
            categories = [dict(r) for r in cur.fetchall()]

            # Top merchants
            cur.execute("""
                SELECT merchant, SUM(debit) as total_spent, COUNT(*) as tx_count
                FROM transactions
                WHERE debit > 0
                GROUP BY merchant
                ORDER BY total_spent DESC
                LIMIT 10
            """)
            merchants = [dict(r) for r in cur.fetchall()]

            # Monthly breakdown
            cur.execute("""
                SELECT substr(transaction_date, 1, 7) as month,
                       SUM(debit) as debit_total,
                       SUM(credit) as credit_total,
                       COUNT(*) as tx_count
                FROM transactions
                GROUP BY substr(transaction_date, 1, 7)
                ORDER BY month ASC
            """)
            monthly = [dict(r) for r in cur.fetchall()]

            return {
                "total_expense": round(total_debit, 2),
                "total_income": round(total_credit, 2),
                "net_balance": round(net_balance, 2),
                "total_transactions": count,
                "start_date": dates["start_date"],
                "end_date": dates["end_date"],
                "categories": categories,
                "top_merchants": merchants,
                "monthly_trend": monthly
            }

    # --- Anomaly Operations ---

    def save_anomalies(self, anomalies: List[Dict[str, Any]]) -> int:
        if not anomalies:
            return 0
        sql = """
            INSERT OR REPLACE INTO anomalies (
                id, transaction_id, anomaly_type, severity, reason,
                historical_baseline, delta_amount, confidence, status, detected_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        rows = [
            (
                a["id"], a["transaction_id"], a["anomaly_type"], a.get("severity", "medium"),
                a["reason"], float(a.get("historical_baseline", 0.0)),
                float(a.get("delta_amount", 0.0)), float(a.get("confidence", 1.0)),
                a.get("status", "flagged"), a.get("detected_at", datetime.now().isoformat())
            )
            for a in anomalies
        ]
        with self.get_connection() as conn:
            conn.executemany(sql, rows)
            conn.commit()
        return len(rows)

    def get_anomalies(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        sql = """
            SELECT a.*, t.transaction_date, t.description, t.merchant, t.debit, t.debit as amount, t.credit, t.category
            FROM anomalies a
            JOIN transactions t ON a.transaction_id = t.id
            WHERE 1=1
        """
        params = []
        if status:
            sql += " AND a.status = ?"
            params.append(status)
        sql += " ORDER BY a.detected_at DESC"

        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]

    # --- Recovery Operations ---

    def save_recovery_record(self, record: Dict[str, Any]) -> str:
        sql = """
            INSERT OR REPLACE INTO recovery_records (
                id, original_transaction_id, potential_amount, confirmed_amount,
                unresolved_amount, status, merchant, notes, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(sql, (
                record["id"],
                record["original_transaction_id"],
                float(record["potential_amount"]),
                float(record.get("confirmed_amount", 0.0)),
                float(record["unresolved_amount"]),
                record["status"],
                record["merchant"],
                record.get("notes"),
                now
            ))
            conn.commit()
        return record["id"]

    def add_recovery_link(self, recovery_id: str, credit_txn_id: str, linked_amount: float, confidence: float = 1.0, notes: str = "", confidence_score: Optional[float] = None) -> str:
        final_conf = confidence_score if confidence_score is not None else confidence
        link_id = f"link_{datetime.now().strftime('%Y%m%d%H%M%S')}_{recovery_id[:6]}"
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO recovery_links (id, recovery_id, credit_transaction_id, linked_amount, confidence_score, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (link_id, recovery_id, credit_txn_id, linked_amount, final_conf, notes))

            # Recalculate confirmed and unresolved amounts for recovery_record
            cur.execute("SELECT SUM(linked_amount) as total_linked FROM recovery_links WHERE recovery_id = ?", (recovery_id,))
            confirmed = cur.fetchone()["total_linked"] or 0.0

            cur.execute("SELECT potential_amount FROM recovery_records WHERE id = ?", (recovery_id,))
            rec = cur.fetchone()
            if rec:
                potential = rec["potential_amount"]
                unresolved = max(0.0, potential - confirmed)
                
                # Determine state
                if unresolved == 0.0 and confirmed > 0.0:
                    status = "confirmed_recovery"
                elif confirmed > 0.0:
                    status = "partially_confirmed"
                else:
                    status = "under_investigation"

                cur.execute("""
                    UPDATE recovery_records
                    SET confirmed_amount = ?, unresolved_amount = ?, status = ?, updated_at = ?
                    WHERE id = ?
                """, (confirmed, unresolved, status, datetime.now().isoformat(), recovery_id))

            conn.commit()
        return link_id

    def get_recovery_records(self) -> List[Dict[str, Any]]:
        sql = """
            SELECT r.*, t.transaction_date as original_date, t.description as original_description,
                   t.reference_id as original_reference
            FROM recovery_records r
            JOIN transactions t ON r.original_transaction_id = t.id
            ORDER BY r.updated_at DESC
        """
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            records = [dict(r) for r in cur.fetchall()]
            
            # Fetch linked credits for each
            for r in records:
                cur.execute("""
                    SELECT rl.*, t.transaction_date as credit_date, t.description as credit_desc,
                           t.credit as credit_amount, t.reference_id as credit_ref
                    FROM recovery_links rl
                    JOIN transactions t ON rl.credit_transaction_id = t.id
                    WHERE rl.recovery_id = ?
                """, (r["id"],))
                r["links"] = [dict(link) for link in cur.fetchall()]
            return records

    def get_recovery_summary(self) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    COALESCE(SUM(potential_amount), 0.0) as total_potential,
                    COALESCE(SUM(confirmed_amount), 0.0) as total_confirmed,
                    COALESCE(SUM(unresolved_amount), 0.0) as total_unresolved,
                    COUNT(*) as total_cases
                FROM recovery_records
            """)
            row = cur.fetchone()
            return {
                "total_potential": round(row["total_potential"], 2),
                "total_confirmed": round(row["total_confirmed"], 2),
                "total_unresolved": round(row["total_unresolved"], 2),
                "total_cases": row["total_cases"]
            }

    # --- Agent Trace & Investigation ---

    def log_investigation(self, inv_id: str, user_query: str, status: str, final_answer: str, language: str = "English"):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO investigations (id, user_query, status, final_answer, language)
                VALUES (?, ?, ?, ?, ?)
            """, (inv_id, user_query, status, final_answer, language))
            conn.commit()

    def log_trace_step(self, inv_id: str, step_index: int, thought: str, tool: str, tool_args: Any, observation: str, decision: str):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO trace_steps (investigation_id, step_index, thought, tool, tool_args, observation, decision)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                inv_id,
                step_index,
                thought,
                tool,
                json.dumps(tool_args) if isinstance(tool_args, (dict, list)) else str(tool_args),
                observation,
                decision
            ))
            conn.commit()

    def get_investigation_trace(self, inv_id: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM trace_steps WHERE investigation_id = ? ORDER BY step_index ASC", (inv_id,))
            return [dict(r) for r in cur.fetchall()]

    def reset_all(self):
        """Reset database tables (used for testing or clean reloads)."""
        with self.get_connection() as conn:
            conn.execute("DELETE FROM trace_steps")
            conn.execute("DELETE FROM investigations")
            conn.execute("DELETE FROM recovery_links")
            conn.execute("DELETE FROM recovery_records")
            conn.execute("DELETE FROM anomalies")
            conn.execute("DELETE FROM user_category_corrections")
            conn.execute("DELETE FROM transactions")
            conn.commit()
