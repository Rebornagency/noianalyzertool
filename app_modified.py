import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import os
import logging
import base64
from typing import Dict, Any, List, Union, Optional
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Import the NOI calculations module
from noi_calculations import calculate_noi_comparisons
# Import config functions for API configuration
from config import get_extraction_api_url, get_api_key, get_openai_api_key
# Import batch processing module
from noi_tool_batch_integration import process_multiple_documents_batch
# Import insights display module
from insights_display import display_insights
# Import centralized helper functions
from utils import format_for_noi_comparison
# Import Reborn logo
from static.reborn_logo import get_reborn_logo_base64

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("noi_analyzer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('noi_analyzer')

# Set page configuration
st.set_page_config(
    page_title="Reborn NOI Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load and apply custom CSS
def load_css():
    with open(os.path.join(os.path.dirname(__file__), "static/style.css")) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Display Reborn logo
def display_logo():
    logo_base64 = get_reborn_logo_base64()
    logo_html = f"""
    <div class="header-container">
        <div class="logo-container">
            <img src="data:image/png;base64,{logo_base64}" width="120">
        </div>
    </div>
    """
    st.markdown(logo_html, unsafe_allow_html=True)

# Apply CSS
load_css()

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "Upload"

if "property_name" not in st.session_state:
    st.session_state.property_name = ""

if "using_sample_data" not in st.session_state:
    st.session_state.using_sample_data = False

# Initialize file upload session states with clear naming
if "current_month_actuals" not in st.session_state:
    st.session_state.current_month_actuals = None

if "prior_month_actuals" not in st.session_state:
    st.session_state.prior_month_actuals = None

if "current_month_budget" not in st.session_state:
    st.session_state.current_month_budget = None

if "prior_year_actuals" not in st.session_state:
    st.session_state.prior_year_actuals = None

# Initialize consolidated data
if "consolidated_data" not in st.session_state:
    st.session_state.consolidated_data = {
        "current_month": None,
        "prior_month": None,
        "budget": None,
        "prior_year": None
    }

if "comparison_results" not in st.session_state:
    st.session_state.comparison_results = {}

if "processed_files" not in st.session_state:
    st.session_state.processed_files = []

# Initialize raw results
if "raw_results" not in st.session_state:
    st.session_state.raw_results = []

# Initialize active tab for results
if "active_results_tab" not in st.session_state:
    st.session_state.active_results_tab = 0

# Initialize selected document and comparison
if "selected_document" not in st.session_state:
    st.session_state.selected_document = None

if "selected_comparison" not in st.session_state:
    st.session_state.selected_comparison = None

# Configure OpenAI API key
if "openai_api_key" not in st.session_state:
    # Get from config
    api_key = get_openai_api_key()
    st.session_state.openai_api_key = api_key

# Configure extraction API URL
if "extraction_api_url" not in st.session_state:
    st.session_state.extraction_api_url = get_extraction_api_url()

# Configure API key for extraction API
if "api_key" not in st.session_state:
    st.session_state.api_key = get_api_key()

def extract_noi_data(file: Any) -> Optional[Dict[str, Any]]:
    """
    Extract NOI data from a single file using the extraction API
    
    Args:
        file: Uploaded file
        
    Returns:
        Extracted data or None if extraction failed
    """
    api_url = st.session_state.extraction_api_url
    api_key = st.session_state.api_key
    
    logger.info(f"Extracting data from {file.name} using API: {api_url}")
    
    try:
        # Create form data with file
        files = {"file": (file.name, file.getvalue(), file.type)}
        headers = {
            "x-api-key": api_key,
            "Authorization": f"Bearer {api_key}"
        }
        
        # Initialize progress
        progress = st.progress(0)
        progress_text = st.empty()
        progress_text.text("Preparing file for extraction...")
        progress.progress(10)
        
        # Send request to API
        with st.spinner(f"Extracting data from {file.name}..."):
            # Update progress
            progress_text.text("Sending file to extraction API...")
            progress.progress(30)
            
            # Add API key as a parameter as well as in headers for redundancy
            params = {"api_key": api_key}
            
            # Log request details for debugging
            logger.info(f"Sending request to {api_url} with API key in headers and params")
            
            # Make the API request with API key in both headers and params
            response = requests.post(api_url, files=files, headers=headers, params=params, timeout=60)
            
            # Update progress
            progress_text.text("Processing API response...")
            progress.progress(70)
        
        # Update progress
        progress_text.text("Finalizing extraction...")
        progress.progress(90)
        
        # Check if request was successful
        if response.status_code == 200:
            # Complete progress
            progress.progress(100)
            progress_text.text("Extraction complete!")
            
            result = response.json()
            logger.info(f"Successfully extracted data from {file.name}")
            return result
        else:
            logger.error(f"API error: {response.status_code} - {response.text}")
            st.error(f"API error: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.Timeout:
        logger.error(f"Request timed out while processing {file.name}")
        st.error(f"Request timed out while processing {file.name}. The file may be too large or complex.")
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error. Could not connect to the extraction API at {st.session_state.extraction_api_url}")
        st.error(f"Connection error. Could not connect to the extraction API at {st.session_state.extraction_api_url}")
        return None
    except Exception as e:
        logger.error(f"Error extracting data: {str(e)}")
        st.error(f"Error extracting data: {str(e)}")
        return None

# This function has been moved to utils/helpers.py and is now imported from utils

def process_document(file: Any, document_type: str) -> bool:
    """
    Process a single document and store the results
    
    Args:
        file: Uploaded file
        document_type: Type of document (current_month, prior_month, budget, prior_year)
        
    Returns:
        True if processing was successful, False otherwise
    """
    if file is None:
        return False
    
    try:
        with st.spinner(f"Processing {file.name}..."):
            result = extract_noi_data(file)
            if result:
                # Handle both dictionary and list response formats
                if isinstance(result, list) and len(result) > 0:
                    # Extract financials from the first item in the list
                    logger.info("API returned a list response, extracting financials from first item")
                    financials = result[0].get("financials", {})
                else:
                    # Handle as dictionary (original behavior)
                    financials = result.get("financials", {})
                
                # Format data for NOI comparison
                formatted_data = format_for_noi_comparison(financials)
                
                # Store in consolidated data
                st.session_state.consolidated_data[document_type] = formatted_data
                
                # Store raw data
                if "raw_data" not in st.session_state:
                    st.session_state.raw_data = {}
                
                st.session_state.raw_data[document_type] = result
                
                st.success(f"Successfully processed {file.name}")
                return True
            else:
                st.error(f"Failed to extract data from {file.name}")
                return False
    except Exception as e:
        st.error(f"Error processing {file.name}: {str(e)}")
        logger.error(f"Error processing {file.name}: {str(e)}")
        return False

def collect_all_files() -> Dict[str, Any]:
    """
    Collect all uploaded files with their document types
    
    Returns:
        Dictionary mapping document types to files
    """
    all_files = {}
    
    # Add current month actuals
    if st.session_state.current_month_actuals:
        all_files["current_month"] = st.session_state.current_month_actuals
    
    # Add prior month actuals
    if st.session_state.prior_month_actuals:
        all_files["prior_month"] = st.session_state.prior_month_actuals
    
    # Add budget files
    if st.session_state.current_month_budget:
        all_files["budget"] = st.session_state.current_month_budget
    
    # Add prior year actuals
    if st.session_state.prior_year_actuals:
        all_files["prior_year"] = st.session_state.prior_year_actuals
    
    return all_files

def process_all_documents() -> Dict[str, Any]:
    """
    Process all uploaded documents with their known document types
    
    Returns:
        Consolidated data dictionary with the structure expected by calculate_noi_comparisons()
    """
    # Initialize consolidated data structure
    consolidated_data = {
        "current_month": None,
        "prior_month": None,
        "budget": None,
        "prior_year": None
    }
    
    # Helper function to handle both dictionary and list response formats
    def extract_financials(result):
        # Check if result is a list
        if isinstance(result, list) and len(result) > 0:
            # Extract financials from the first item in the list
            logger.info("API returned a list response, extracting financials from first item")
            return result[0].get("financials", {})
        else:
            # Handle as dictionary (original behavior)
            return result.get("financials", {})
    
    # Process current month actuals
    if st.session_state.current_month_actuals:
        result = extract_noi_data(st.session_state.current_month_actuals)
        if result:
            financials = extract_financials(result)
            formatted_data = format_for_noi_comparison(financials)
            consolidated_data["current_month"] = formatted_data
            st.success(f"Successfully processed current month actuals: {st.session_state.current_month_actuals.name}")
    
    # Process prior month actuals
    if st.session_state.prior_month_actuals:
        result = extract_noi_data(st.session_state.prior_month_actuals)
        if result:
            financials = extract_financials(result)
            formatted_data = format_for_noi_comparison(financials)
            consolidated_data["prior_month"] = formatted_data
            st.success(f"Successfully processed prior month actuals: {st.session_state.prior_month_actuals.name}")
    
    # Process budget files
    if st.session_state.current_month_budget:
        result = extract_noi_data(st.session_state.current_month_budget)
        if result:
            financials = extract_financials(result)
            formatted_data = format_for_noi_comparison(financials)
            consolidated_data["budget"] = formatted_data
            st.success(f"Successfully processed budget: {st.session_state.current_month_budget.name}")
    
    # Process prior year actuals
    if st.session_state.prior_year_actuals:
        result = extract_noi_data(st.session_state.prior_year_actuals)
        if result:
            financials = extract_financials(result)
            formatted_data = format_for_noi_comparison(financials)
            consolidated_data["prior_year"] = formatted_data
            st.success(f"Successfully processed prior year actuals: {st.session_state.prior_year_actuals.name}")
    
    # Store in session state
    st.session_state.consolidated_data = consolidated_data
    
    return consolidated_data

def display_noi_comparisons(comparison_results: Dict[str, Any]):
    """
    Display NOI comparisons in the Streamlit app
    
    Args:
        comparison_results: Results from calculate_noi_comparisons()
    """
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["Current Month", "Budget Comparison", "Year-over-Year", "Month-over-Month"])
    
    # Tab 1: Current Month
    with tab1:
        if "current" in comparison_results:
            current = comparison_results["current"]
            
            st.subheader("Current Month Overview")
            
            # Create columns for metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Revenue", f"${current['revenue']:,.2f}")
            
            with col2:
                st.metric("Expenses", f"${current['expense']:,.2f}")
            
            with col3:
                st.metric("NOI", f"${current['noi']:,.2f}")
            
            # Create pie chart for revenue vs expenses
            fig = px.pie(
                values=[current['revenue'], current['expense']],
                names=['Revenue', 'Expenses'],
                title="Revenue vs Expenses",
                color_discrete_sequence=["#0099ff", "#FF0000"]
            )
            st.plotly_chart(fig)
        else:
            st.info("No current month data available")
    
    # Tab 2: Budget Comparison
    with tab2:
        if "actual_vs_budget" in comparison_results:
            budget_comp = comparison_results["actual_vs_budget"]
            
            st.subheader("Actual vs Budget Comparison")
            
            # Create columns for metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Actual NOI", f"${comparison_results['current']['noi']:,.2f}")
            
            with col2:
                st.metric("Budget NOI", f"${budget_comp['budget_noi']:,.2f}")
            
            with col3:
                st.metric("Variance", 
                         f"${budget_comp['noi_variance']:,.2f}", 
                         f"{budget_comp['noi_percent_variance']:.2f}%",
                         delta_color="normal" if budget_comp['noi_variance'] >= 0 else "inverse")
            
            # Create bar chart for comparison
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=['Revenue', 'Expenses', 'NOI'],
                y=[comparison_results['current']['revenue'], 
                   comparison_results['current']['expense'], 
                   comparison_results['current']['noi']],
                name='Actual',
                marker_color='#0099ff'
            ))
            
            fig.add_trace(go.Bar(
                x=['Revenue', 'Expenses', 'NOI'],
                y=[budget_comp['budget_revenue'], 
                   budget_comp['budget_expense'], 
                   budget_comp['budget_noi']],
                name='Budget',
                marker_color='#4472C4'
            ))
            
            fig.update_layout(
                title="Actual vs Budget Comparison",
                xaxis_title="Category",
                yaxis_title="Amount ($)",
                barmode='group',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white')
            )
            
            st.plotly_chart(fig)
        else:
            st.info("No budget comparison data available")
    
    # Tab 3: Year-over-Year
    with tab3:
        if "year_vs_year" in comparison_results:
            yoy_comp = comparison_results["year_vs_year"]
            
            st.subheader("Year-over-Year Comparison")
            
            # Create columns for metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Current NOI", f"${comparison_results['current']['noi']:,.2f}")
            
            with col2:
                st.metric("Prior Year NOI", f"${yoy_comp['prior_year_noi']:,.2f}")
            
            with col3:
                st.metric("YoY Change", 
                         f"${yoy_comp['noi_change']:,.2f}", 
                         f"{yoy_comp['noi_percent_change']:.2f}%",
                         delta_color="normal" if yoy_comp['noi_change'] >= 0 else "inverse")
            
            # Create bar chart for comparison
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=['Revenue', 'Expenses', 'NOI'],
                y=[comparison_results['current']['revenue'], 
                   comparison_results['current']['expense'], 
                   comparison_results['current']['noi']],
                name='Current',
                marker_color='#0099ff'
            ))
            
            fig.add_trace(go.Bar(
                x=['Revenue', 'Expenses', 'NOI'],
                y=[yoy_comp['prior_year_revenue'], 
                   yoy_comp['prior_year_expense'], 
                   yoy_comp['prior_year_noi']],
                name='Prior Year',
                marker_color='#4472C4'
            ))
            
            fig.update_layout(
                title="Year-over-Year Comparison",
                xaxis_title="Category",
                yaxis_title="Amount ($)",
                barmode='group',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white')
            )
            
            st.plotly_chart(fig)
        else:
            st.info("No year-over-year comparison data available")
    
    # Tab 4: Month-over-Month
    with tab4:
        if "month_vs_prior" in comparison_results:
            mom_comp = comparison_results["month_vs_prior"]
            
            st.subheader("Month-over-Month Comparison")
            
            # Create columns for metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Current NOI", f"${comparison_results['current']['noi']:,.2f}")
            
            with col2:
                st.metric("Prior Month NOI", f"${mom_comp['prior_month_noi']:,.2f}")
            
            with col3:
                st.metric("MoM Change", 
                         f"${mom_comp['noi_change']:,.2f}", 
                         f"{mom_comp['noi_percent_change']:.2f}%",
                         delta_color="normal" if mom_comp['noi_change'] >= 0 else "inverse")
            
            # Create bar chart for comparison
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=['Revenue', 'Expenses', 'NOI'],
                y=[comparison_results['current']['revenue'], 
                   comparison_results['current']['expense'], 
                   comparison_results['current']['noi']],
                name='Current',
                marker_color='#0099ff'
            ))
            
            fig.add_trace(go.Bar(
                x=['Revenue', 'Expenses', 'NOI'],
                y=[mom_comp['prior_month_revenue'], 
                   mom_comp['prior_month_expense'], 
                   mom_comp['prior_month_noi']],
                name='Prior Month',
                marker_color='#4472C4'
            ))
            
            fig.update_layout(
                title="Month-over-Month Comparison",
                xaxis_title="Category",
                yaxis_title="Amount ($)",
                barmode='group',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white')
            )
            
            st.plotly_chart(fig)
        else:
            st.info("No month-over-month comparison data available")

def check_api_status(api_url: Optional[str] = None) -> bool:
    """
    Check if the extraction API is running and accessible
    
    Args:
        api_url: Optional URL to check, defaults to the URL in session state
        
    Returns:
        True if API is accessible, False otherwise
    """
    if api_url is None:
        api_url = st.session_state.extraction_api_url
    
    try:
        # Get base URL (without the /extract endpoint)
        base_url = api_url.rsplit('/', 1)[0] if '/extract' in api_url else api_url
        health_url = f"{base_url}/health"
        
        # Try to connect to the API health endpoint first
        try:
            response = requests.get(health_url, timeout=5)
            if response.status_code < 400:
                st.success("✅ API is running and accessible!")
                return True
        except:
            # If health endpoint doesn't exist, fall back to POST request to main endpoint
            pass
            
        # Use POST request with empty payload instead of GET
        headers = {"Content-Type": "application/json"}
        empty_payload = {}
        
        # Send a POST request with empty payload
        response = requests.post(api_url, json=empty_payload, headers=headers, timeout=5)
        
        # Even a 405 error means the API is running, just not accepting empty POST requests
        if response.status_code < 500:
            st.success("✅ API is running and accessible!")
            return True
        else:
            st.warning(f"⚠️ API returned status code {response.status_code}. It may not be functioning correctly.")
            return False
    except requests.exceptions.Timeout:
        st.error("❌ API request timed out. The server might be slow or unresponsive.")
        return False
    except requests.exceptions.ConnectionError:
        st.error("❌ Connection error. Could not connect to the API.")
        return False
    except Exception as e:
        st.error(f"❌ Error checking API status: {str(e)}")
        return False

def show_upload_page():
    """Show the upload page with clearly labeled file upload slots for each document type"""
    # Display logo
    display_logo()
    
    # Main title
    st.markdown("<h1>Upload Financial Documents</h1>", unsafe_allow_html=True)
    
    # Property name input
    property_name = st.text_input(
        "Property Name",
        value=st.session_state.property_name,
        help="Enter the name of the property for this analysis"
    )
    
    if property_name != st.session_state.property_name:
        st.session_state.property_name = property_name
    
    # Sample data option
    use_sample = st.checkbox(
        "Use example documents",
        value=st.session_state.using_sample_data,
        help="Use built-in sample data for demonstration"
    )
    
    if use_sample != st.session_state.using_sample_data:
        st.session_state.using_sample_data = use_sample
    
    if not use_sample:
        # File uploads with clear labels
        st.markdown("<h2>Upload Required Documents</h2>", unsafe_allow_html=True)
        st.markdown("<p>To analyze NOI, please provide multipdocuments</p>", unsafe_allow_html=True)
        
        # Current Month Actuals
        with st.container():
            st.markdown("""
            <div class="file-label">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-file-earmark-text" viewBox="0 0 16 16">
                    <path d="M5.5 7a.5.5 0 0 0 0 1h5a.5.5 0 0 0 0-1h-5zM5 9.5a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 0 1h-5a.5.5 0 0 1-.5-.5zm0 2a.5.5 0 0 1 .5-.5h2a.5.5 0 0 1 0 1h-2a.5.5 0 0 1-.5-.5z"/>
                    <path d="M9.5 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V4.5L9.5 0zm0 1v2A1.5 1.5 0 0 0 11 4.5h2V14a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1h5.5z"/>
                </svg>
                <span>Current Rent Roll</span>
            </div>
            """, unsafe_allow_html=True)
            
            current_month_actuals = st.file_uploader(
                "Drag and drop files here",
                type=["csv", "xlsx", "xls", "pdf", "txt"],
                key="current_month_actuals_uploader",
                help="Upload a document containing current month revenue and expense data"
            )
            
            if current_month_actuals is not None:
                st.session_state.current_month_actuals = current_month_actuals
                st.success(f"Current month actuals uploaded: {current_month_actuals.name}")
                
                # Preview for CSV and Excel files
                if current_month_actuals.name.endswith(('.csv', '.xlsx', '.xls')):
                    try:
                        if current_month_actuals.name.endswith('.csv'):
                            df = pd.read_csv(current_month_actuals)
                        else:
                            df = pd.read_excel(current_month_actuals)
                        st.dataframe(df.head())
                    except Exception as e:
                        st.error(f"Error previewing file: {str(e)}")
                else:
                    st.info(f"Preview not available for {current_month_actuals.name}. File will be processed during extraction.")
        
        # Prior Month Actuals
        with st.container():
            st.markdown("""
            <div class="file-label">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-file-earmark-text" viewBox="0 0 16 16">
                    <path d="M5.5 7a.5.5 0 0 0 0 1h5a.5.5 0 0 0 0-1h-5zM5 9.5a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 0 1h-5a.5.5 0 0 1-.5-.5zm0 2a.5.5 0 0 1 .5-.5h2a.5.5 0 0 1 0 1h-2a.5.5 0 0 1-.5-.5z"/>
                    <path d="M9.5 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V4.5L9.5 0zm0 1v2A1.5 1.5 0 0 0 11 4.5h2V14a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1h5.5z"/>
                </svg>
                <span>Prior Month Statement</span>
            </div>
            """, unsafe_allow_html=True)
            
            prior_month_actuals = st.file_uploader(
                "Drag and drop files here",
                type=["csv", "xlsx", "xls", "pdf", "txt"],
                key="prior_month_actuals_uploader",
                help="Upload a document containing prior month revenue and expense data"
            )
            
            if prior_month_actuals is not None:
                st.session_state.prior_month_actuals = prior_month_actuals
                st.success(f"Prior month actuals uploaded: {prior_month_actuals.name}")
                
                # Preview for CSV and Excel files
                if prior_month_actuals.name.endswith(('.csv', '.xlsx', '.xls')):
                    try:
                        if prior_month_actuals.name.endswith('.csv'):
                            df = pd.read_csv(prior_month_actuals)
                        else:
                            df = pd.read_excel(prior_month_actuals)
                        st.dataframe(df.head())
                    except Exception as e:
                        st.error(f"Error previewing file: {str(e)}")
                else:
                    st.info(f"Preview not available for {prior_month_actuals.name}. File will be processed during extraction.")
        
        # Budget
        with st.container():
            st.markdown("""
            <div class="file-label">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-file-earmark-text" viewBox="0 0 16 16">
                    <path d="M5.5 7a.5.5 0 0 0 0 1h5a.5.5 0 0 0 0-1h-5zM5 9.5a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 0 1h-5a.5.5 0 0 1-.5-.5zm0 2a.5.5 0 0 1 .5-.5h2a.5.5 0 0 1 0 1h-2a.5.5 0 0 1-.5-.5z"/>
                    <path d="M9.5 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V4.5L9.5 0zm0 1v2A1.5 1.5 0 0 0 11 4.5h2V14a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1h5.5z"/>
                </svg>
                <span>Budget Document</span>
            </div>
            """, unsafe_allow_html=True)
            
            current_month_budget = st.file_uploader(
                "Drag and drop files here",
                type=["csv", "xlsx", "xls", "pdf", "txt"],
                key="current_month_budget_uploader",
                help="Upload a document containing budget data for the current month"
            )
            
            if current_month_budget is not None:
                st.session_state.current_month_budget = current_month_budget
                st.success(f"Budget uploaded: {current_month_budget.name}")
                
                # Preview for CSV and Excel files
                if current_month_budget.name.endswith(('.csv', '.xlsx', '.xls')):
                    try:
                        if current_month_budget.name.endswith('.csv'):
                            df = pd.read_csv(current_month_budget)
                        else:
                            df = pd.read_excel(current_month_budget)
                        st.dataframe(df.head())
                    except Exception as e:
                        st.error(f"Error previewing file: {str(e)}")
                else:
                    st.info(f"Preview not available for {current_month_budget.name}. File will be processed during extraction.")
        
        # Prior Year Actuals
        with st.container():
            st.markdown("""
            <div class="file-label">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-file-earmark-text" viewBox="0 0 16 16">
                    <path d="M5.5 7a.5.5 0 0 0 0 1h5a.5.5 0 0 0 0-1h-5zM5 9.5a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 0 1h-5a.5.5 0 0 1-.5-.5zm0 2a.5.5 0 0 1 .5-.5h2a.5.5 0 0 1 0 1h-2a.5.5 0 0 1-.5-.5z"/>
                    <path d="M9.5 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V4.5L9.5 0zm0 1v2A1.5 1.5 0 0 0 11 4.5h2V14a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1h5.5z"/>
                </svg>
                <span>Prior Year Statement</span>
            </div>
            """, unsafe_allow_html=True)
            
            prior_year_actuals = st.file_uploader(
                "Drag and drop files here",
                type=["csv", "xlsx", "xls", "pdf", "txt"],
                key="prior_year_actuals_uploader",
                help="Upload a document containing prior year revenue and expense data"
            )
            
            if prior_year_actuals is not None:
                st.session_state.prior_year_actuals = prior_year_actuals
                st.success(f"Prior year actuals uploaded: {prior_year_actuals.name}")
                
                # Preview for CSV and Excel files
                if prior_year_actuals.name.endswith(('.csv', '.xlsx', '.xls')):
                    try:
                        if prior_year_actuals.name.endswith('.csv'):
                            df = pd.read_csv(prior_year_actuals)
                        else:
                            df = pd.read_excel(prior_year_actuals)
                        st.dataframe(df.head())
                    except Exception as e:
                        st.error(f"Error previewing file: {str(e)}")
                else:
                    st.info(f"Preview not available for {prior_year_actuals.name}. File will be processed during extraction.")
        
        # Calculate NOI button
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Check if at least current month actuals are uploaded
        if st.session_state.current_month_actuals is not None:
            if st.button("Calculate NOI", key="calculate_noi_button"):
                # Process documents and calculate NOI
                with st.spinner("Processing documents and calculating NOI..."):
                    # Process all documents
                    consolidated_data = process_all_documents()
                    
                    # Calculate NOI comparisons
                    comparison_results = calculate_noi_comparisons(consolidated_data)
                    
                    # Generate insights with GPT
                    try:
                        # Import the GPT insights generator
                        from ai_insights_gpt import generate_insights_with_gpt
                        
                        # Generate insights
                        property_name = st.session_state.property_name
                        insights = generate_insights_with_gpt(comparison_results, property_name)
                        
                        # Store in session state
                        st.session_state.insights = insights
                        st.success("AI insights generated successfully!")
                    except Exception as e:
                        st.warning(f"Could not automatically generate insights: {str(e)}")
                        st.session_state.insights = None
                    
                    # Store in session state
                    st.session_state.consolidated_data = consolidated_data
                    st.session_state.comparison_results = comparison_results
                    
                    # Navigate to results page
                    st.session_state.page = "Results"
                    st.experimental_rerun()
        else:
            # Show disabled button with tooltip
            st.markdown("""
            <div title="Please upload at least the current month actuals document">
                <button class="stButton" style="opacity: 0.6; cursor: not-allowed;">Calculate NOI</button>
            </div>
            """, unsafe_allow_html=True)
            st.info("Please upload at least the current month actuals document to calculate NOI.")
    else:
        # Use sample data
        st.info("Using sample data for demonstration purposes.")
        
        if st.button("Calculate NOI with Sample Data", key="calculate_sample_button"):
            with st.spinner("Processing sample data..."):
                # Set a default property name if none is provided
                if not st.session_state.property_name:
                    st.session_state.property_name = "Sample Property"
                
                # Load sample data (this would be replaced with actual sample data)
                sample_data = {
                    "current_month": {
                        "revenue": 100000,
                        "expense": 60000,
                        "noi": 40000
                    },
                    "prior_month": {
                        "revenue": 95000,
                        "expense": 58000,
                        "noi": 37000
                    },
                    "budget": {
                        "revenue": 105000,
                        "expense": 62000,
                        "noi": 43000
                    },
                    "prior_year": {
                        "revenue": 90000,
                        "expense": 55000,
                        "noi": 35000
                    }
                }
                
                # Calculate NOI comparisons
                comparison_results = calculate_noi_comparisons(sample_data)
                
                # Generate insights with GPT
                try:
                    # Import the GPT insights generator
                    from ai_insights_gpt import generate_insights_with_gpt
                    
                    # Generate insights
                    property_name = st.session_state.property_name
                    insights = generate_insights_with_gpt(comparison_results, property_name)
                    
                    # Store in session state
                    st.session_state.insights = insights
                    st.success("AI insights generated successfully!")
                except Exception as e:
                    st.warning(f"Could not automatically generate insights: {str(e)}")
                    st.session_state.insights = None
                
                # Store in session state
                st.session_state.consolidated_data = sample_data
                st.session_state.comparison_results = comparison_results
                
                # Navigate to results page
                st.session_state.page = "Results"
                st.experimental_rerun()

def show_results_page():
    """Show the results page with NOI comparisons and AI-generated insights"""
    # Display logo
    display_logo()
    
    st.title("NOI Analysis Results")
    
    # Display property name if available
    if st.session_state.property_name:
        st.header(f"Property: {st.session_state.property_name}")
    
    # Check if we have comparison results
    if st.session_state.comparison_results:
        # Display NOI comparisons
        display_noi_comparisons(st.session_state.comparison_results)
        
        # Display AI-generated insights if available
        if "insights" in st.session_state and st.session_state.insights:
            st.markdown("---")
            display_insights(st.session_state.insights, st.session_state.property_name)
            
            # Add button to regenerate insights if needed (optional)
            if st.button("Regenerate Insights", key="regenerate_optional"):
                with st.spinner("Regenerating insights with GPT..."):
                    try:
                        # Import the GPT insights generator
                        from ai_insights_gpt import generate_insights_with_gpt
                        
                        # Generate insights
                        property_name = st.session_state.property_name
                        insights = generate_insights_with_gpt(st.session_state.comparison_results, property_name)
                        
                        # Store in session state
                        st.session_state.insights = insights
                        
                        st.success("Insights regenerated successfully!")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error generating insights: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
        else:
            # This should rarely happen since insights are now generated automatically
            # But we'll keep this as a fallback
            st.warning("AI-generated insights were not automatically generated. Generating them now...")
            
            # Automatically generate insights without requiring button press
            with st.spinner("Generating insights with GPT..."):
                try:
                    # Import the GPT insights generator
                    from ai_insights_gpt import generate_insights_with_gpt
                    
                    # Generate insights
                    property_name = st.session_state.property_name
                    insights = generate_insights_with_gpt(st.session_state.comparison_results, property_name)
                    
                    # Store in session state
                    st.session_state.insights = insights
                    
                    st.success("Insights generated successfully!")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error generating insights: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
        
        # Add button to return to upload page
        if st.button("Return to Upload Page"):
            st.session_state.page = "Upload"
            st.experimental_rerun()
    else:
        st.warning("No comparison results available. Please process documents first.")
        
        # Add button to return to upload page
        if st.button("Return to Upload Page"):
            st.session_state.page = "Upload"
            st.experimental_rerun()

def show_api_status_page():
    """Show the API status page"""
    # Display logo
    display_logo()
    
    st.title("API Status")
    
    # Check API status
    st.subheader("Extraction API Status")
    api_status = check_api_status()
    
    # Display API configuration
    st.subheader("API Configuration")
    st.write(f"API URL: {st.session_state.extraction_api_url}")
    
    # Add button to return to upload page
    if st.button("Return to Upload Page"):
        st.session_state.page = "Upload"
        st.experimental_rerun()

# Main app logic
def main():
    """Main application logic"""
    # Create sidebar for navigation
    with st.sidebar:
        # Display logo in sidebar
        st.markdown(f"""
        <div style="display: flex; justify-content: center; margin-bottom: 20px;">
            <img src="data:image/png;base64,{get_reborn_logo_base64()}" width="80">
        </div>
        """, unsafe_allow_html=True)
        
        st.title("NOI Analyzer")
        
        # Navigation
        st.subheader("Navigation")
        
        # Upload page button
        if st.button("Upload Documents", key="nav_upload"):
            st.session_state.page = "Upload"
            st.experimental_rerun()
        
        # Results page button
        if st.button("View Results", key="nav_results"):
            st.session_state.page = "Results"
            st.experimental_rerun()
        
        # API status page button
        if st.button("API Status", key="nav_api"):
            st.session_state.page = "API"
            st.experimental_rerun()
        
        # Add separator
        st.markdown("---")
        
        # Add API status indicator
        st.subheader("API Status")
        try:
            # Quick check of API status
            api_url = st.session_state.extraction_api_url
            response = requests.head(api_url, timeout=2)
            if response.status_code < 500:
                st.success("✅ API is accessible")
            else:
                st.warning("⚠️ API may have issues")
        except:
            st.error("❌ API is not accessible")
    
    # Display the appropriate page based on session state
    if st.session_state.page == "Upload":
        show_upload_page()
    elif st.session_state.page == "Results":
        show_results_page()
    elif st.session_state.page == "API":
        show_api_status_page()
    else:
        # Default to upload page
        show_upload_page()

if __name__ == "__main__":
    main()
