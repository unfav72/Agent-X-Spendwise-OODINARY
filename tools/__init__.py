"""
Spendwise AI - Tool Registry & Execution Interface
Implements the Tool base class contract and registers all 10 financial auditor tools + starter tools.
"""

from typing import Dict, Any, Optional

class Tool:
    name = "tool"
    description = ""
    args_doc = "{}"

    def execute(self, **kwargs):
        raise NotImplementedError

# Import function implementations
from .transaction_search import execute as run_transaction_search
from .spending_analytics import execute as run_spending_analytics
from .anomaly_detector import execute as run_anomaly_detector
from .duplicate_finder import execute as run_duplicate_candidate_finder
from .recurring_detector import execute as run_recurring_payment_detector
from .refund_matcher import execute as run_refund_matcher
from .budget_simulator import execute as run_budget_simulator
from .transaction_comparator import execute as run_transaction_comparator
from .statement_data_validator import execute as run_statement_data_validator
from .report_exporter import execute as run_report_exporter

# Tool Wrapper Classes satisfying the AgentX Tool contract
class TransactionSearch(Tool):
    name = "transaction_search"
    description = "Search transactions by date range, merchant, category, query text, amount threshold, or debit/credit."
    args_doc = '{"query": str, "category": str, "merchant": str, "min_amount": float, "max_amount": float, "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD", "txn_type": "debit"|"credit", "limit": int}'

    def execute(self, **kwargs):
        return run_transaction_search(**kwargs)

class SpendingAnalytics(Tool):
    name = "spending_analytics"
    description = "Calculates monthly spending breakdown, category totals, month-over-month deltas, and spending velocity increases."
    args_doc = '{"target_month": "YYYY-MM"}'

    def execute(self, **kwargs):
        return run_spending_analytics(**kwargs)

class AnomalyDetector(Tool):
    name = "anomaly_detector"
    description = "Scans transactions for statistical spikes (>2.5σ), high-value outliers, and sudden velocity bursts."
    args_doc = '{"threshold_multiplier": float}'

    def execute(self, **kwargs):
        return run_anomaly_detector(**kwargs)

class DuplicateCandidateFinder(Tool):
    name = "duplicate_candidate_finder"
    description = "Finds candidate duplicate charges with matching amount and merchant within a short window (0-3 days)."
    args_doc = '{"max_days_gap": int}'

    def execute(self, **kwargs):
        return run_duplicate_candidate_finder(**kwargs)

class RecurringPaymentDetector(Tool):
    name = "recurring_payment_detector"
    description = "Detects recurring subscriptions, cadence intervals (monthly/weekly), and computes monthly and annualized commitments."
    args_doc = '{"min_occurrences": int}'

    def execute(self, **kwargs):
        return run_recurring_payment_detector(**kwargs)

class RefundMatcher(Tool):
    name = "refund_matcher"
    description = "Investigates refund candidates, matches original debit charges to verified credits, and tracks unresolved balances."
    args_doc = '{"merchant": str, "original_tx_id": str}'

    def execute(self, **kwargs):
        return run_refund_matcher(**kwargs)

class BudgetSimulator(Tool):
    name = "budget_simulator"
    description = "Performs deterministic simulation of category cuts (percentage or cap) and calculates monthly & annual hypothetical savings."
    args_doc = '{"reductions": {"category": percentage_float}, "flat_caps": {"category": cap_float}}'

    def execute(self, **kwargs):
        return run_budget_simulator(**kwargs)

class TransactionComparator(Tool):
    name = "transaction_comparator"
    description = "Compares spending between two date ranges or between months."
    args_doc = '{"period_a_start": "YYYY-MM-DD", "period_a_end": "YYYY-MM-DD", "period_b_start": "YYYY-MM-DD", "period_b_end": "YYYY-MM-DD", "category": str}'

    def execute(self, **kwargs):
        return run_transaction_comparator(**kwargs)

class StatementDataValidator(Tool):
    name = "statement_data_validator"
    description = "Validates loaded statement health, missing merchants, missing reference IDs, and negative amounts."
    args_doc = '{}'

    def execute(self, **kwargs):
        return run_statement_data_validator(**kwargs)

class ReportExporter(Tool):
    name = "report_exporter"
    description = "Compiles all financial metrics, anomalies, recurring payments, and recovery statuses into an audit payload."
    args_doc = '{}'

    def execute(self, **kwargs):
        return run_report_exporter(**kwargs)


def build_tools():
    """Build and return dictionary of all available tools."""
    financial_tools = [
        TransactionSearch(),
        SpendingAnalytics(),
        AnomalyDetector(),
        DuplicateCandidateFinder(),
        RecurringPaymentDetector(),
        RefundMatcher(),
        BudgetSimulator(),
        TransactionComparator(),
        StatementDataValidator(),
        ReportExporter()
    ]

    # Include starter utilities if present
    extra_tools = []
    try:
        from tools.calculator import Calculator
        from tools.data_query import ListFiles, ReadFile, SqlQuery
        from tools.web_search import WebSearch
        extra_tools = [Calculator(), ListFiles(), ReadFile(), SqlQuery(), WebSearch()]
    except Exception:
        pass

    tools_dict = {t.name: t for t in financial_tools + extra_tools}

    # Add friendly aliases
    aliases = {
        "duplicate_finder": tools_dict["duplicate_candidate_finder"],
        "recurring_detector": tools_dict["recurring_payment_detector"],
        "refund_detector": tools_dict["refund_matcher"],
        "search_transactions": tools_dict["transaction_search"],
        "analytics": tools_dict["spending_analytics"]
    }
    for alias, tool_obj in aliases.items():
        tools_dict[alias] = tool_obj

    return tools_dict
