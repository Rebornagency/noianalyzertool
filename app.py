"""
NOI Analyzer - Main Streamlit Application
This application analyzes Net Operating Income (NOI) from financial documents,
providing detailed metrics, visualizations, and AI-powered insights.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
import base64

# Import custom modules
from noi_tool_batch_integration import process_multiple_documents_batch
from noi_calculations import calculate_noi_comparisons
from ai_insights_gpt import generate_insights_with_gpt
from insights_display import display_insights
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
    initial_sidebar_state="collapsed"
)

# Load CSS
def load_css():
    with open(os.path.join("static", "style.css")) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Apply CSS
load_css()

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

def initialize_session_state():
    """Initialize session state variables"""
    if 'current_month_actuals' not in st.session_state:
        st.session_state.current_month_actuals = None
    if 'prior_month_actuals' not in st.session_state:
        st.session_state.prior_month_actuals = None
    if 'current_month_budget' not in st.session_state:
        st.session_state.current_month_budget = None
    if 'prior_year_actuals' not in st.session_state:
        st.session_state.prior_year_actuals = None
    if 'consolidated_data' not in st.session_state:
        st.session_state.consolidated_data = None
    if 'processing_completed' not in st.session_state:
        st.session_state.processing_completed = False
    if 'comparison_results' not in st.session_state:
        st.session_state.comparison_results = None
    if 'insights' not in st.session_state:
        st.session_state.insights = None
    if 'property_name' not in st.session_state:
        st.session_state.property_name = ""
    if 'use_example_data' not in st.session_state:
        st.session_state.use_example_data = False
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "upload"

def reset_session_state():
    """Reset session state variables"""
    st.session_state.current_month_actuals = None
    st.session_state.prior_month_actuals = None
    st.session_state.current_month_budget = None
    st.session_state.prior_year_actuals = None
    st.session_state.consolidated_data = None
    st.session_state.processing_completed = False
    st.session_state.comparison_results = None
    st.session_state.insights = None
    st.session_state.current_page = "upload"
    st.rerun()

def display_upload_page():
    """Display the styled upload page based on the provided design"""
    # Display logo
    display_logo()
    
    st.markdown("<h1 style='font-size: 3.5rem; font-weight: 500; margin-bottom: 1rem;'>Upload Financial Documents</h1>", unsafe_allow_html=True)
    
    # Property Name input
    st.markdown("<p style='font-size: 1.2rem; margin-bottom: 0.5rem;'>Property Name</p>", unsafe_allow_html=True)
    st.session_state.property_name = st.text_input("", value=st.session_state.property_name, label_visibility="collapsed")
    
    # Use example documents checkbox
    st.checkbox("Use example documents", key="use_example_data")
    
    st.markdown("<h2 style='font-size: 1.8rem; margin-top: 2rem; margin-bottom: 1rem;'>Upload Required Documents</h2>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 1.1rem; margin-bottom: 2rem;'>To analyze NOI, please provide multiple documents</p>", unsafe_allow_html=True)

    # Current Month Actuals upload (required)
    st.markdown("<div class='document-label'><span style='display: flex; align-items: center;'><span style='font-size: 1.3rem; margin-right: 10px;'>📄</span> Current Month Actuals</span></div>", unsafe_allow_html=True)
    st.session_state.current_month_actuals = st.file_uploader(
        "Upload Current Month Actuals (Required)",
        type=["pdf", "xlsx", "xls", "csv", "txt"],
        key="current_month_actuals_uploader",
        label_visibility="collapsed"
    )
    
    # Prior Month Actuals upload (optional)
    st.markdown("<div class='document-label'><span style='display: flex; align-items: center;'><span style='font-size: 1.3rem; margin-right: 10px;'>📄</span> Prior Month Actuals</span></div>", unsafe_allow_html=True)
    st.session_state.prior_month_actuals = st.file_uploader(
        "Upload Prior Month Actuals (Optional)",
        type=["pdf", "xlsx", "xls", "csv", "txt"],
        key="prior_month_actuals_uploader",
        label_visibility="collapsed"
    )
    
    # Current Month Budget upload (optional)
    st.markdown("<div class='document-label'><span style='display: flex; align-items: center;'><span style='font-size: 1.3rem; margin-right: 10px;'>📄</span> Current Month Budget</span></div>", unsafe_allow_html=True)
    st.session_state.current_month_budget = st.file_uploader(
        "Upload Current Month Budget (Optional)",
        type=["pdf", "xlsx", "xls", "csv", "txt"],
        key="current_month_budget_uploader",
        label_visibility="collapsed"
    )
    
    # Prior Year Actuals upload (optional)
    st.markdown("<div class='document-label'><span style='display: flex; align-items: center;'><span style='font-size: 1.3rem; margin-right: 10px;'>📄</span> Prior Year Actuals</span></div>", unsafe_allow_html=True)
    st.session_state.prior_year_actuals = st.file_uploader(
        "Upload Prior Year Actuals (Optional)",
        type=["pdf", "xlsx", "xls", "csv", "txt"],
        key="prior_year_actuals_uploader",
        label_visibility="collapsed"
    )
    
    # Calculate NOI button
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        calculate_button = st.button(
            "Calculate NOI", 
            type="primary", 
            disabled=not st.session_state.current_month_actuals and not st.session_state.use_example_data
        )
    
    if calculate_button:
        if st.session_state.use_example_data:
            # Use example data logic here
            st.info("Using example data for demonstration purposes.")
            process_documents()
        elif st.session_state.current_month_actuals:
            with st.spinner("Processing documents..."):
                process_documents()
        else:
            st.error("Please upload Current Month Actuals document or use example data.")

def process_documents():
    """Process uploaded documents and store results in session state"""
    try:
        # Prepare list of files and document type mapping
        files = []
        document_types = {}
        
        if st.session_state.current_month_actuals:
            files.append(st.session_state.current_month_actuals)
            document_types[st.session_state.current_month_actuals.name] = "current_month_actuals"
            
        if st.session_state.prior_month_actuals:
            files.append(st.session_state.prior_month_actuals)
            document_types[st.session_state.prior_month_actuals.name] = "prior_month_actuals"
            
        if st.session_state.current_month_budget:
            files.append(st.session_state.current_month_budget)
            document_types[st.session_state.current_month_budget.name] = "current_month_budget"
            
        if st.session_state.prior_year_actuals:
            files.append(st.session_state.prior_year_actuals)
            document_types[st.session_state.prior_year_actuals.name] = "prior_year_actuals"
        
        # Process documents in batch
        result = process_multiple_documents_batch(
            files=files,
            property_name=st.session_state.property_name,
            document_types=document_types
        )
        
        if result.get("success", False):
            st.session_state.consolidated_data = result.get("consolidated_data", {})
            st.session_state.comparison_results = result.get("comparison_results", {})
            st.session_state.processing_completed = True
            
            # Generate insights if we have comparison results
            if st.session_state.comparison_results:
                with st.spinner("Generating AI insights..."):
                    st.session_state.insights = generate_insights_with_gpt(
                        st.session_state.comparison_results,
                        property_name=st.session_state.property_name
                    )
            
            st.success("Documents processed successfully!")
            st.session_state.current_page = "results"
            st.rerun()
        else:
            st.error(f"Failed to process documents: {result.get('error', 'Unknown error')}")
            st.session_state.processing_completed = False
    except Exception as e:
        logger.error(f"Error processing documents: {str(e)}")
        st.error(f"Error processing documents: {str(e)}")
        st.session_state.processing_completed = False

def display_results():
    """Display the results of the NOI analysis"""
    # Display logo
    display_logo()
    
    st.markdown("<h1 style='font-size: 2.5rem; font-weight: 500; margin-bottom: 1rem;'>NOI Analysis Results</h1>", unsafe_allow_html=True)
    
    if st.session_state.property_name:
        st.markdown(f"<h2 style='font-size: 1.8rem; margin-bottom: 2rem;'>Property: {st.session_state.property_name}</h2>", unsafe_allow_html=True)
    
    # Display tabs for different sections
    tab1, tab2, tab3 = st.tabs([
        "Summary Metrics", 
        "Detailed Comparisons", 
        "AI Insights"
    ])
    
    with tab1:
        display_summary_metrics()
    
    with tab2:
        display_detailed_comparisons()
    
    with tab3:
        if st.session_state.insights:
            display_insights(st.session_state.insights, st.session_state.property_name)
        else:
            st.info("AI insights are not available. Please make sure you have processed all necessary documents.")
    
    # Add a button to go back to the upload page
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("Analyze New Property", type="primary"):
            reset_session_state()

def display_summary_metrics():
    """Display summary metrics and visualizations"""
    results = st.session_state.comparison_results
    current_data = results.get("current", {})
    
    if not current_data:
        st.warning("No current month data available for summary metrics.")
        return
    
    # Create a dashboard with summary metrics
    st.subheader("Current Month Overview")
    
    # Key financial metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Total Revenue",
            value=f"${current_data.get('revenue', 0):,.2f}"
        )
    
    with col2:
        st.metric(
            label="Total Expenses",
            value=f"${current_data.get('expense', 0):,.2f}"
        )
    
    with col3:
        st.metric(
            label="NOI",
            value=f"${current_data.get('noi', 0):,.2f}"
        )
    
    # Create a simple breakdown chart
    st.subheader("Financial Breakdown")
    
    # Create data for visualization
    data = {
        "Category": ["Revenue", "Expenses", "NOI"],
        "Amount": [
            current_data.get("revenue", 0),
            current_data.get("expense", 0),
            current_data.get("noi", 0)
        ]
    }
    
    df = pd.DataFrame(data)
    
    # Create a bar chart
    fig = px.bar(
        df,
        x="Category",
        y="Amount",
        color="Category",
        color_discrete_map={
            "Revenue": "#0e4de3",
            "Expenses": "#4682B4",
            "NOI": "#32CD32"
        },
        title="Current Month Financial Summary"
    )
    
    fig.update_layout(
        yaxis_title="Amount ($)",
        xaxis_title="",
        legend_title="Category",
        height=400,
        paper_bgcolor="#1a1f29",
        plot_bgcolor="#1a1f29",
        font=dict(color="#ffffff")
    )
    
    # Add dollar formatting to y-axis
    fig.update_yaxes(tickprefix="$", tickformat=",.0f", color="#ffffff")
    fig.update_xaxes(color="#ffffff")
    
    st.plotly_chart(fig, use_container_width=True)

def display_detailed_comparisons():
    """Display detailed comparisons between periods"""
    results = st.session_state.comparison_results
    
    # Check if we have comparison data
    mom_data = results.get("month_vs_prior", {})
    budget_data = results.get("actual_vs_budget", {})
    yoy_data = results.get("year_vs_year", {})
    
    if not any([mom_data, budget_data, yoy_data]):
        st.warning("No comparison data available. Please upload additional documents for comparison.")
        return
    
    # Create tabs for different comparisons
    tab1, tab2, tab3 = st.tabs([
        "Month vs Prior Month", 
        "Actual vs Budget", 
        "Year vs Prior Year"
    ])
    
    # Month vs Prior Month
    with tab1:
        if mom_data:
            st.subheader("Current Month vs Prior Month")
            
            # Key metrics comparison
            col1, col2, col3 = st.columns(3)
            
            with col1:
                revenue_change = mom_data.get("revenue_change", 0)
                revenue_pct = mom_data.get("revenue_percent_change", 0)
                st.metric(
                    label="Revenue Change",
                    value=f"${revenue_change:,.2f}",
                    delta=f"{revenue_pct:.2f}%"
                )
            
            with col2:
                expense_change = mom_data.get("expense_change", 0)
                expense_pct = mom_data.get("expense_percent_change", 0)
                st.metric(
                    label="Expense Change",
                    value=f"${expense_change:,.2f}",
                    delta=f"{expense_pct:.2f}%",
                    delta_color="inverse"  # Lower expenses are better
                )
            
            with col3:
                noi_change = mom_data.get("noi_change", 0)
                noi_pct = mom_data.get("noi_percent_change", 0)
                st.metric(
                    label="NOI Change",
                    value=f"${noi_change:,.2f}",
                    delta=f"{noi_pct:.2f}%"
                )
            
            # Create comparison chart
            create_comparison_chart(
                current_value=results.get("current", {}).get("noi", 0),
                comparison_value=mom_data.get("noi_prior", 0),
                title="NOI: Current Month vs Prior Month",
                current_label="Current Month",
                comparison_label="Prior Month"
            )
        else:
            st.info("No prior month data available for comparison.")
    
    # Actual vs Budget
    with tab2:
        if budget_data:
            st.subheader("Actual vs Budget")
            
            # Key metrics comparison
            col1, col2, col3 = st.columns(3)
            
            with col1:
                revenue_var = budget_data.get("revenue_variance", 0)
                revenue_pct = budget_data.get("revenue_percent_variance", 0)
                st.metric(
                    label="Revenue Variance",
                    value=f"${revenue_var:,.2f}",
                    delta=f"{revenue_pct:.2f}%"
                )
            
            with col2:
                expense_var = budget_data.get("expense_variance", 0)
                expense_pct = budget_data.get("expense_percent_variance", 0)
                st.metric(
                    label="Expense Variance",
                    value=f"${expense_var:,.2f}",
                    delta=f"{expense_pct:.2f}%",
                    delta_color="inverse"  # Lower expenses are better
                )
            
            with col3:
                noi_var = budget_data.get("noi_variance", 0)
                noi_pct = budget_data.get("noi_percent_variance", 0)
                st.metric(
                    label="NOI Variance",
                    value=f"${noi_var:,.2f}",
                    delta=f"{noi_pct:.2f}%"
                )
            
            # Create comparison chart
            create_comparison_chart(
                current_value=results.get("current", {}).get("noi", 0),
                comparison_value=budget_data.get("noi_budget", 0),
                title="NOI: Actual vs Budget",
                current_label="Actual",
                comparison_label="Budget"
            )
        else:
            st.info("No budget data available for comparison.")
    
    # Year vs Prior Year
    with tab3:
        if yoy_data:
            st.subheader("Current Year vs Prior Year")
            
            # Key metrics comparison
            col1, col2, col3 = st.columns(3)
            
            with col1:
                revenue_change = yoy_data.get("revenue_change", 0)
                revenue_pct = yoy_data.get("revenue_percent_change", 0)
                st.metric(
                    label="Revenue YoY Change",
                    value=f"${revenue_change:,.2f}",
                    delta=f"{revenue_pct:.2f}%"
                )
            
            with col2:
                expense_change = yoy_data.get("expense_change", 0)
                expense_pct = yoy_data.get("expense_percent_change", 0)
                st.metric(
                    label="Expense YoY Change",
                    value=f"${expense_change:,.2f}",
                    delta=f"{expense_pct:.2f}%",
                    delta_color="inverse"  # Lower expenses are better
                )
            
            with col3:
                noi_change = yoy_data.get("noi_change", 0)
                noi_pct = yoy_data.get("noi_percent_change", 0)
                st.metric(
                    label="NOI YoY Change",
                    value=f"${noi_change:,.2f}",
                    delta=f"{noi_pct:.2f}%"
                )
            
            # Create comparison chart
            create_comparison_chart(
                current_value=results.get("current", {}).get("noi", 0),
                comparison_value=yoy_data.get("noi_prior_year", 0),
                title="NOI: Current Year vs Prior Year",
                current_label="Current Year",
                comparison_label="Prior Year"
            )
        else:
            st.info("No prior year data available for comparison.")

def create_comparison_chart(current_value, comparison_value, title, current_label, comparison_label):
    """Create a comparison chart for two values"""
    
    # Create data for bar chart
    data = {
        "Category": [current_label, comparison_label],
        "NOI": [current_value, comparison_value]
    }
    
    df = pd.DataFrame(data)
    
    # Create a bar chart
    fig = px.bar(
        df,
        x="Category",
        y="NOI",
        color="Category",
        color_discrete_map={
            current_label: "#0e4de3",
            comparison_label: "#4682B4"
        },
        title=title
    )
    
    fig.update_layout(
        yaxis_title="NOI ($)",
        xaxis_title="",
        legend_title="Period",
        height=400,
        paper_bgcolor="#1a1f29",
        plot_bgcolor="#1a1f29",
        font=dict(color="#ffffff")
    )
    
    # Add dollar formatting to y-axis
    fig.update_yaxes(tickprefix="$", tickformat=",.0f", color="#ffffff")
    fig.update_xaxes(color="#ffffff")
    
    st.plotly_chart(fig, use_container_width=True)

def main():
    """Main application function"""
    # Initialize session state
    initialize_session_state()
    
    # Display the appropriate page based on the current state
    if not st.session_state.processing_completed or st.session_state.current_page == "upload":
        display_upload_page()
    else:
        display_results()

if __name__ == "__main__":
    main()