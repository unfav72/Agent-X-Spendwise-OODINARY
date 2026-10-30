"""
Spendwise AI Tool: budget_simulator
Performs deterministic financial projections for spending reductions and category rebalancing.
"""

from typing import Dict, Any, List, Optional
from database.repository import Repository

def execute(
    reductions: Optional[Dict[str, float]] = None, # e.g. {"Food delivery": 15.0, "Shopping": 20.0} (percentage cuts)
    flat_caps: Optional[Dict[str, float]] = None,   # e.g. {"Entertainment": 1000.0} (max cap)
    repository: Optional[Repository] = None
) -> Dict[str, Any]:
    repo = repository or Repository()
    overview = repo.get_spending_overview()
    categories = overview.get("categories", [])
    monthly_trend = overview.get("monthly_trend", [])

    num_months = max(1, len(monthly_trend))
    
    # Calculate average monthly spend per category
    cat_avg_monthly: Dict[str, float] = {}
    for c in categories:
        cat_name = c["category"]
        total_spent = c["total_spent"]
        cat_avg_monthly[cat_name] = total_spent / num_months

    if not reductions:
        reductions = {}
    if not flat_caps:
        flat_caps = {}

    simulated_categories = []
    total_current_monthly = sum(cat_avg_monthly.values())
    total_projected_monthly = 0.0

    for cat_name, current_monthly in cat_avg_monthly.items():
        proposed_monthly = current_monthly
        reduction_pct = reductions.get(cat_name, 0.0)
        flat_cap = flat_caps.get(cat_name)

        if reduction_pct > 0:
            cut = current_monthly * (reduction_pct / 100.0)
            proposed_monthly = max(0.0, current_monthly - cut)
        elif flat_cap is not None:
            proposed_monthly = min(current_monthly, float(flat_cap))
            cut = current_monthly - proposed_monthly
            reduction_pct = round((cut / current_monthly * 100), 1) if current_monthly > 0 else 0.0
        else:
            cut = 0.0

        monthly_saving = current_monthly - proposed_monthly
        annual_saving = monthly_saving * 12.0
        total_projected_monthly += proposed_monthly

        simulated_categories.append({
            "category": cat_name,
            "current_monthly_spend": round(current_monthly, 2),
            "proposed_monthly_spend": round(proposed_monthly, 2),
            "monthly_expected_saving": round(monthly_saving, 2),
            "annualized_expected_saving": round(annual_saving, 2),
            "percentage_reduction": round(reduction_pct, 1),
            "is_modified": monthly_saving > 0
        })

    total_monthly_saving = total_current_monthly - total_projected_monthly
    total_annual_saving = total_monthly_saving * 12.0
    overall_cut_pct = round((total_monthly_saving / total_current_monthly * 100), 1) if total_current_monthly > 0 else 0.0

    # Sort so modified categories appear first
    simulated_categories.sort(key=lambda x: (not x["is_modified"], -x["monthly_expected_saving"]))

    return {
        "status": "success",
        "current_total_monthly_spend": round(total_current_monthly, 2),
        "projected_total_monthly_spend": round(total_projected_monthly, 2),
        "monthly_hypothetical_savings": round(total_monthly_saving, 2),
        "annualized_hypothetical_savings": round(total_annual_saving, 2),
        "overall_percentage_reduction": overall_cut_pct,
        "category_breakdown": simulated_categories,
        "accounting_notice": "Hypothetical projected savings do not constitute realized cash flow and exclude pending refunds.",
        "summary": (
            f"Budget Simulation: Trimming proposed categories achieves ₹{round(total_monthly_saving, 2)}/month "
            f"in projected hypothetical savings (₹{round(total_annual_saving, 2)}/year), an overall {overall_cut_pct}% reduction."
        )
    }

