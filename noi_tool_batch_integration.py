import streamlit as st
import pandas as pd
import logging
import json
from typing import Dict, Any, Optional

from noi_calculations import calculate_noi_comparisons
from ai_insights_gpt import generate_insights_with_gpt
from insights_display import display_insights
from ai_extraction import extract_noi_data
from utils.helpers import format_for_noi_comparison

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("noi_analyzer_enhanced.log"), # New log file name
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('noi_tool_batch_integration')

def process_all_documents() -> Dict[str, Any]:
    """
    Process all uploaded documents using the enhanced extraction API.

    Returns:
        Consolidated data dictionary with the DETAILED structure for each document type.
    """
    # Initialize consolidated data structure
    consolidated_data = {
        "current_month": None,
        "prior_month": None,
        "budget": None,
        "prior_year": None
    }
    processed_ok = True # Flag to track if all essential processing worked

    # Process current month actuals
    if st.session_state.current_month_actuals:
        st.write(f"Processing Current Month: {st.session_state.current_month_actuals.name}...")
        result = extract_noi_data(st.session_state.current_month_actuals, "current_month_actuals")
        if result:
            # Use the new formatter
            formatted_data = format_for_noi_comparison(result)
            consolidated_data["current_month"] = formatted_data
            st.success(f"Processed Current Month: {st.session_state.current_month_actuals.name}")
        else:
             st.error(f"Failed to process Current Month: {st.session_state.current_month_actuals.name}")
             processed_ok = False # Mark failure

    # Process prior month actuals
    if st.session_state.prior_month_actuals:
        st.write(f"Processing Prior Month: {st.session_state.prior_month_actuals.name}...")
        result = extract_noi_data(st.session_state.prior_month_actuals, "prior_month_actuals")
        if result:
            formatted_data = format_for_noi_comparison(result)
            consolidated_data["prior_month"] = formatted_data
            st.success(f"Processed Prior Month: {st.session_state.prior_month_actuals.name}")
        else:
             st.error(f"Failed to process Prior Month: {st.session_state.prior_month_actuals.name}")
             # Allow continuing even if optional files fail

    # Process budget files
    if st.session_state.current_month_budget:
        st.write(f"Processing Budget: {st.session_state.current_month_budget.name}...")
        result = extract_noi_data(st.session_state.current_month_budget, "current_month_budget")
        if result:
            formatted_data = format_for_noi_comparison(result)
            consolidated_data["budget"] = formatted_data
            st.success(f"Processed Budget: {st.session_state.current_month_budget.name}")
        else:
             st.error(f"Failed to process Budget: {st.session_state.current_month_budget.name}")


    # Process prior year actuals
    if st.session_state.prior_year_actuals:
        st.write(f"Processing Prior Year: {st.session_state.prior_year_actuals.name}...")
        result = extract_noi_data(st.session_state.prior_year_actuals, "prior_year_actuals")
        if result:
            formatted_data = format_for_noi_comparison(result)
            consolidated_data["prior_year"] = formatted_data
            st.success(f"Processed Prior Year: {st.session_state.prior_year_actuals.name}")
        else:
             st.error(f"Failed to process Prior Year: {st.session_state.prior_year_actuals.name}")


    # Store in session state
    st.session_state.consolidated_data = consolidated_data
    st.session_state.processing_completed = processed_ok # Store completion status

    # Log the final consolidated structure (optional)
    # logger.debug(f"Final consolidated data structure: {json.dumps(consolidated_data, default=str)}")

    return consolidated_data
