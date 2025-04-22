"""
Helper functions for the NOI Analyzer application
"""

import logging
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('helpers')

def format_for_noi_comparison(financials: Dict[str, Any]) -> Dict[str, float]:
    """
    Format financial data for NOI comparison calculations
    
    Args:
        financials: Financial data from API response
        
    Returns:
        Formatted data with standardized revenue, expense, and NOI fields
    """
    # Initialize result with default values
    formatted_data = {
        "revenue": 0.0,
        "expense": 0.0,  # Note: NOI calculations expect "expense" not "expenses"
        "noi": 0.0
    }
    
    # Extract the relevant values with defaults of 0 for missing values
    revenue = financials.get('total_revenue', 0)
    expenses = financials.get('total_expenses', 0)
    noi = financials.get('net_operating_income', 0)
    
    # Handle None values
    revenue = 0.0 if revenue is None else float(revenue)
    expenses = 0.0 if expenses is None else float(expenses)
    noi = 0.0 if noi is None else float(noi)
    
    # If NOI is not provided but we have revenue and expenses, calculate it
    if noi == 0 and revenue != 0 and expenses != 0:
        noi = revenue - expenses
    
    # Update the formatted data
    formatted_data["revenue"] = revenue
    formatted_data["expense"] = expenses
    formatted_data["noi"] = noi
    
    return formatted_data

def determine_document_type(filename: str, result: Dict[str, Any]) -> str:
    """
    Determine the document type based on filename and content
    
    Args:
        filename: Name of the file
        result: Extraction result
        
    Returns:
        Document type (current_month, prior_month, budget, prior_year)
    """
    filename = filename.lower()
    
    # Try to determine from filename first
    if "budget" in filename:
        return "budget"
    elif "prior" in filename or "previous" in filename:
        if "year" in filename:
            return "prior_year"
        else:
            return "prior_month"
    elif "current" in filename or "actual" in filename:
        return "current_month"
    
    # If not determined from filename, try to use document_type from result
    doc_type = result.get("document_type", "").lower()
    if "budget" in doc_type:
        return "budget"
    elif "prior year" in doc_type or "previous year" in doc_type:
        return "prior_year"
    elif "prior" in doc_type or "previous" in doc_type:
        return "prior_month"
    elif "current" in doc_type or "actual" in doc_type:
        return "current_month"
    
    # Default to current_month if can't determine
    return "current_month"

def format_currency(value: float) -> str:
    """
    Format a value as currency
    
    Args:
        value: Numeric value to format
        
    Returns:
        Formatted currency string
    """
    return f"${value:,.2f}"

def format_percent(value: float) -> str:
    """
    Format a value as percentage
    
    Args:
        value: Numeric value to format
        
    Returns:
        Formatted percentage string
    """
    return f"{value:.2f}%"