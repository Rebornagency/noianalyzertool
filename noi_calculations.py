import logging
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('noi_calculations')

def calculate_noi_comparisons(consolidated_data: Dict[str, Optional[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Calculate detailed NOI comparisons based on the enhanced consolidated data.

    Args:
        consolidated_data: Dictionary containing the formatted detailed financial data
                           for 'current_month', 'prior_month', 'budget', 'prior_year'.
                           Values can be None if data is missing.

    Returns:
        A dictionary containing comparison results for various metrics (EGI, Vacancy, OpEx, NOI).
    """
    comparison_results = {}
    current_data = consolidated_data.get("current_month")

    # Store current month detailed data if available
    if current_data:
        comparison_results["current"] = current_data # Store the whole formatted dict

    # --- Helper function for safe division ---
    def safe_percent_change(current, previous):
        if previous is None or previous == 0:
            return 0.0 # Avoid division by zero
        # Handle None for current value
        current_val = current if current is not None else 0.0
        return ((current_val - previous) / previous) * 100

    # --- Calculate Month vs Prior Month Comparison ---
    prior_month_data = consolidated_data.get("prior_month")
    if current_data and prior_month_data:
        mom = {}
        # Compare key metrics
        for key in ["gpr", "vacancy_loss", "other_income", "egi", "opex", "noi"]:
            current_val = current_data.get(key, 0.0)
            prior_val = prior_month_data.get(key, 0.0)
            mom[f"{key}_prior"] = prior_val
            mom[f"{key}_change"] = current_val - prior_val
            mom[f"{key}_percent_change"] = safe_percent_change(current_val, prior_val)
        comparison_results["month_vs_prior"] = mom

    # --- Calculate Actual vs Budget Comparison ---
    budget_data = consolidated_data.get("budget")
    if current_data and budget_data:
        avb = {}
        # Compare key metrics
        for key in ["gpr", "vacancy_loss", "other_income", "egi", "opex", "noi"]:
            actual_val = current_data.get(key, 0.0)
            budget_val = budget_data.get(key, 0.0)
            avb[f"{key}_budget"] = budget_val
            avb[f"{key}_variance"] = actual_val - budget_val
            # Note: Variance % for expenses often inverted (lower is better) - handle in display
            avb[f"{key}_percent_variance"] = safe_percent_change(actual_val, budget_val)
        comparison_results["actual_vs_budget"] = avb

    # --- Calculate Actual vs Prior Year Comparison ---
    prior_year_data = consolidated_data.get("prior_year")
    if current_data and prior_year_data:
        yoy = {}
        # Compare key metrics
        for key in ["gpr", "vacancy_loss", "other_income", "egi", "opex", "noi"]:
            current_val = current_data.get(key, 0.0)
            prior_val = prior_year_data.get(key, 0.0)
            yoy[f"{key}_prior_year"] = prior_val
            yoy[f"{key}_change"] = current_val - prior_val
            yoy[f"{key}_percent_change"] = safe_percent_change(current_val, prior_val)
        comparison_results["year_vs_year"] = yoy

    logger.info(f"Calculated detailed comparisons: {list(comparison_results.keys())}")
    # logger.debug(f"Comparison results structure: {json.dumps(comparison_results, default=str)}")
    return comparison_results
