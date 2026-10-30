"""
Spendwise AI - Transaction Service
Coordinates transactions, categorization, querying, and data integrity.
"""

from typing import List, Dict, Any, Optional, Tuple
from database.repository import Repository
from ingestion import ingest_file

class TransactionService:
    def __init__(self, repository: Optional[Repository] = None):
        self.repo = repository or Repository()

    def ingest_statement(self, file_path: str) -> Tuple[int, Dict[str, Any]]:
        corrections = self.repo.get_user_category_corrections()
        records, report = ingest_file(file_path, user_corrections=corrections)
        count = self.repo.insert_transactions(records)
        return count, report

    def search_transactions(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        merchant: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        txn_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        return self.repo.query_transactions(
            query_text=query,
            category=category,
            merchant=merchant,
            min_amount=min_amount,
            max_amount=max_amount,
            start_date=start_date,
            end_date=end_date,
            txn_type=txn_type,
            limit=limit,
            offset=offset
        )

    def get_overview(self) -> Dict[str, Any]:
        return self.repo.get_spending_overview()

    def update_category(self, transaction_id: str, new_category: str) -> bool:
        return self.repo.update_transaction_category(transaction_id, new_category)

