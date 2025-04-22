"""
NOI Calculations Module for Streamlit App
This module provides functions for calculating NOI comparisons between different periods.
"""

import logging
from typing import Dict, Any, Optional

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
        A dictionary containing comparison results for various metrics (revenue, expenses, NOI).
    """
    logger.info("Calculating NOI comparisons")
    
    # Extract data for each period
    current_month = consolidated_data.get('current_month')
    prior_month = consolidated_data.get('prior_month')
    budget = consolidated_data.get('budget')
    prior_year = consolidated_data.get('prior_year')
    
    # Initialize results dictionary
    results = {
        "current": {},
        "month_vs_prior": {},
        "actual_vs_budget": {},
        "year_vs_year": {}
    }
    
    # Function to calculate percent change safely
    def safe_percent_change(current, previous):
        """Calculate percent change, handling division by zero"""
        if previous is None or current is None:
            return None
        if previous == 0:
            return 100.0 if current > 0 else -100.0 if current < 0 else 0.0
        return ((current - previous) / abs(previous)) * 100.0
    
    # Current month metrics
    if current_month:
        results["current"] = {
            "revenue": current_month.get("total_revenue", 0),
            "expense": current_month.get("total_expenses", 0),
            "noi": current_month.get("net_operating_income", 0)
        }
    
    # Month vs Prior Month comparison
    if current_month and prior_month:
        current_revenue = current_month.get("total_revenue", 0)
        prior_revenue = prior_month.get("total_revenue", 0)
        revenue_change = current_revenue - prior_revenue
        revenue_percent = safe_percent_change(current_revenue, prior_revenue)
        
        current_expense = current_month.get("total_expenses", 0)
        prior_expense = prior_month.get("total_expenses", 0)
        expense_change = current_expense - prior_expense
        expense_percent = safe_percent_change(current_expense, prior_expense)
        
        current_noi = current_month.get("net_operating_income", 0)
        prior_noi = prior_month.get("net_operating_income", 0)
        noi_change = current_noi - prior_noi
        noi_percent = safe_percent_change(current_noi, prior_noi)
        
        results["month_vs_prior"] = {
            "revenue_current": current_revenue,
            "revenue_prior": prior_revenue,
            "revenue_change": revenue_change,
            "revenue_percent_change": revenue_percent,
            
            "expense_current": current_expense,
            "expense_prior": prior_expense,
            "expense_change": expense_change,
            "expense_percent_change": expense_percent,
            
            "noi_current": current_noi,
            "noi_prior": prior_noi,
            "noi_change": noi_change,
            "noi_percent_change": noi_percent
        }
    
    # Actual vs Budget comparison
    if current_month and budget:
        current_revenue = current_month.get("total_revenue", 0)
        budget_revenue = budget.get("total_revenue", 0)
        revenue_variance = current_revenue - budget_revenue
        revenue_percent = safe_percent_change(current_revenue, budget_revenue)
        
        current_expense = current_month.get("total_expenses", 0)
        budget_expense = budget.get("total_expenses", 0)
        expense_variance = current_expense - budget_expense
        expense_percent = safe_percent_change(current_expense, budget_expense)
        
        current_noi = current_month.get("net_operating_income", 0)
        budget_noi = budget.get("net_operating_income", 0)
        noi_variance = current_noi - budget_noi
        noi_percent = safe_percent_change(current_noi, budget_noi)
        
        results["actual_vs_budget"] = {
            "revenue_actual": current_revenue,
            "revenue_budget": budget_revenue,
            "revenue_variance": revenue_variance,
            "revenue_percent_variance": revenue_percent,
            
            "expense_actual": current_expense,
            "expense_budget": budget_expense,
            "expense_variance": expense_variance,
            "expense_percent_variance": expense_percent,
            
            "noi_actual": current_noi,
            "noi_budget": budget_noi,
            "noi_variance": noi_variance,
            "noi_percent_variance": noi_percent
        }
    
    # Year vs Prior Year comparison
    if current_month and prior_year:
        current_revenue = current_month.get("total_revenue", 0)
        prior_revenue = prior_year.get("total_revenue", 0)
        revenue_change = current_revenue - prior_revenue
        revenue_percent = safe_percent_change(current_revenue, prior_revenue)
        
        current_expense = current_month.get("total_expenses", 0)
        prior_expense = prior_year.get("total_expenses", 0)
        expense_change = current_expense - prior_expense
        expense_percent = safe_percent_change(current_expense, prior_expense)
        
        current_noi = current_month.get("net_operating_income", 0)
        prior_noi = prior_year.get("net_operating_income", 0)
        noi_change = current_noi - prior_noi
        noi_percent = safe_percent_change(current_noi, prior_noi)
        
        results["year_vs_year"] = {
            "revenue_current": current_revenue,
            "revenue_prior_year": prior_revenue,
            "revenue_change": revenue_change,
            "revenue_percent_change": revenue_percent,
            
            "expense_current": current_expense,
            "expense_prior_year": prior_expense,
            "expense_change": expense_change,
            "expense_percent_change": expense_percent,
            
            "noi_current": current_noi,
            "noi_prior_year": prior_noi,
            "noi_change": noi_change,
            "noi_percent_change": noi_percent
        }
    
    logger.info("NOI comparisons calculated successfully")
    return results