import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Import modules
from config import get_openai_api_key, get_extraction_api_url, get_api_key
from noi_calculations import calculate_noi_comparisons
from ai_insights_gpt import generate_insights_with_gpt
from insights_display import display_insights
from noi_tool_batch_integration import process_all_documents

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("noi_analyzer_enhanced.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('app')

# Set page config
st.set_page_config(
    page_title="NOI Analyzer Enhanced",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables if they don't exist
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

def display_noi_comparisons(comparison_results: Dict[str, Any]):
    """
    Display DETAILED NOI comparisons in the Streamlit app.

    Args:
        comparison_results: Results from calculate_noi_comparisons() using detailed data.
    """

    current_data = comparison_results.get("current")
    if not current_data:
        st.warning("No current month data available to display comparisons.")
        return

    st.header("Financial Performance Overview")

    # --- Key Metrics Section ---
    st.subheader("Key Performance Indicators (Current Period)")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Eff. Gross Income (EGI)", f"${current_data.get('egi', 0):,.2f}")
    with col2:
        # Calculate Vacancy Rate = Vacancy Loss / GPR (handle division by zero)
        gpr = current_data.get('gpr', 0)
        vacancy_loss = current_data.get('vacancy_loss', 0)
        vacancy_rate = (vacancy_loss / gpr * 100) if gpr else 0
        st.metric("Vacancy & Credit Loss %", f"{vacancy_rate:.1f}%", f"-${vacancy_loss:,.2f}", delta_color="inverse")
    with col3:
        # Calculate OpEx Ratio = Total OpEx / EGI (handle division by zero)
        egi = current_data.get('egi', 0)
        opex = current_data.get('opex', 0)
        opex_ratio = (opex / egi * 100) if egi else 0
        st.metric("Operating Expense Ratio", f"{opex_ratio:.1f}%", f"${opex:,.2f}", delta_color="inverse")
    with col4:
        st.metric("Net Operating Income (NOI)", f"${current_data.get('noi', 0):,.2f}")

    st.markdown("---")

    # --- Comparison Tabs ---
    st.header("Comparative Analysis")
    tab_titles = ["Current vs Budget", "Current vs Prior Year", "Current vs Prior Month"]
    tabs = st.tabs(tab_titles)

    # Helper to display comparison metrics
    def display_comparison_tab(tab_data, prior_key_suffix, name_suffix):
        if not tab_data:
            st.info(f"No {name_suffix} data available for comparison.")
            return

        st.subheader(f"Current vs {name_suffix}")
        metrics = ["GPR", "Vacancy Loss", "Other Income", "EGI", "Total OpEx", "NOI"]
        data_keys = ["gpr", "vacancy_loss", "other_income", "egi", "opex", "noi"]

        df_data = []
        for key, name in zip(data_keys, metrics):
            current_val = current_data.get(key, 0.0)
            prior_val = tab_data.get(f"{key}_{prior_key_suffix}", tab_data.get(f"{key}_budget", 0.0))
            change_val = tab_data.get(f"{key}_change", tab_data.get(f"{key}_variance", 0.0))
            percent_change = tab_data.get(f"{key}_percent_change", tab_data.get(f"{key}_percent_variance", 0.0))
            df_data.append({
                "Metric": name,
                "Current": current_val,
                name_suffix: prior_val,
                "Change ($)": change_val,
                "Change (%)": percent_change
            })

        # Create DataFrame for display
        df = pd.DataFrame(df_data)
        
        # Format DataFrame for display
        df_display = df.copy()
        df_display["Current"] = df_display["Current"].apply(lambda x: f"${x:,.2f}")
        df_display[name_suffix] = df_display[name_suffix].apply(lambda x: f"${x:,.2f}")
        df_display["Change ($)"] = df_display["Change ($)"].apply(lambda x: f"${x:,.2f}")
        df_display["Change (%)"] = df_display["Change (%)"].apply(lambda x: f"{x:.1f}%")
        
        # Display table
        st.dataframe(df_display, use_container_width=True)
        
        # Create bar chart for visual comparison
        fig = go.Figure()
        
        # Add current period bars
        fig.add_trace(go.Bar(
            x=df["Metric"],
            y=df["Current"],
            name="Current",
            marker_color='rgb(55, 83, 109)'
        ))
        
        # Add comparison period bars
        fig.add_trace(go.Bar(
            x=df["Metric"],
            y=df[name_suffix],
            name=name_suffix,
            marker_color='rgb(26, 118, 255)'
        ))
        
        # Update layout
        fig.update_layout(
            title=f"Current vs {name_suffix} Comparison",
            xaxis_tickfont_size=14,
            yaxis=dict(
                title='Amount ($)',
                titlefont_size=16,
                tickfont_size=14,
            ),
            legend=dict(
                x=0,
                y=1.0,
                bgcolor='rgba(255, 255, 255, 0)',
                bordercolor='rgba(255, 255, 255, 0)'
            ),
            barmode='group',
            bargap=0.15,
            bargroupgap=0.1
        )
        
        # Display chart
        st.plotly_chart(fig, use_container_width=True)

    # Display each comparison tab
    with tabs[0]:  # Budget tab
        avb = comparison_results.get("actual_vs_budget")
        display_comparison_tab(avb, "budget", "Budget")
        
    with tabs[1]:  # Prior Year tab
        yoy = comparison_results.get("year_vs_year")
        display_comparison_tab(yoy, "prior_year", "Prior Year")
        
    with tabs[2]:  # Prior Month tab
        mom = comparison_results.get("month_vs_prior")
        display_comparison_tab(mom, "prior", "Prior Month")

def main():
    # App title and description
    st.title("NOI Analyzer Enhanced")
    st.markdown("""
    This application analyzes Net Operating Income (NOI) from financial documents, 
    providing detailed comparisons and AI-generated insights.
    """)
    
    # Sidebar for file uploads and settings
    with st.sidebar:
        st.header("Document Upload")
        st.markdown("Upload your financial documents for analysis.")
        
        # Current Month Actuals (Required)
        st.subheader("Current Month Actuals (Required)")
        current_month_actuals = st.file_uploader(
            "Upload current month actuals",
            type=["pdf", "xlsx", "xls", "csv"],
            key="current_month_actuals_uploader"
        )
        if current_month_actuals:
            st.session_state.current_month_actuals = current_month_actuals
            st.success(f"✅ {current_month_actuals.name}")
        
        # Prior Month Actuals (Optional)
        st.subheader("Prior Month Actuals (Optional)")
        prior_month_actuals = st.file_uploader(
            "Upload prior month actuals",
            type=["pdf", "xlsx", "xls", "csv"],
            key="prior_month_actuals_uploader"
        )
        if prior_month_actuals:
            st.session_state.prior_month_actuals = prior_month_actuals
            st.success(f"✅ {prior_month_actuals.name}")
        
        # Current Month Budget (Optional)
        st.subheader("Current Month Budget (Optional)")
        current_month_budget = st.file_uploader(
            "Upload current month budget",
            type=["pdf", "xlsx", "xls", "csv"],
            key="current_month_budget_uploader"
        )
        if current_month_budget:
            st.session_state.current_month_budget = current_month_budget
            st.success(f"✅ {current_month_budget.name}")
        
        # Prior Year Actuals (Optional)
        st.subheader("Prior Year Actuals (Optional)")
        prior_year_actuals = st.file_uploader(
            "Upload prior year actuals",
            type=["pdf", "xlsx", "xls", "csv"],
            key="prior_year_actuals_uploader"
        )
        if prior_year_actuals:
            st.session_state.prior_year_actuals = prior_year_actuals
            st.success(f"✅ {prior_year_actuals.name}")
        
        # Settings section
        st.header("Settings")
        property_name = st.text_input("Property Name (Optional)", "")
        
        # API Configuration
        with st.expander("API Configuration"):
            api_url = st.text_input("Extraction API URL", get_extraction_api_url())
            api_key = st.text_input("API Key", get_api_key(), type="password")
            openai_api_key = st.text_input("OpenAI API Key", get_openai_api_key(), type="password")
        
        # Process button
        process_button = st.button("Process Documents")
        if process_button:
            if not st.session_state.current_month_actuals:
                st.error("Current Month Actuals is required.")
            else:
                st.session_state.processing_completed = False
                st.session_state.comparison_results = None
                st.session_state.insights = None
                
                # Process documents
                with st.spinner("Processing documents..."):
                    consolidated_data = process_all_documents()
                    
                    # Calculate comparisons if processing was successful
                    if st.session_state.processing_completed:
                        st.session_state.comparison_results = calculate_noi_comparisons(consolidated_data)
                        
                        # Generate insights if OpenAI API key is provided
                        if openai_api_key and len(openai_api_key) > 10:
                            st.session_state.insights = generate_insights_with_gpt(
                                st.session_state.comparison_results,
                                property_name
                            )
                
                # Rerun to update the main content area
                st.rerun()
    
    # Main content area
    if st.session_state.processing_completed and st.session_state.comparison_results:
        # Display NOI comparisons
        display_noi_comparisons(st.session_state.comparison_results)
        
        # Display AI insights if available
        if st.session_state.insights:
            display_insights(st.session_state.insights, property_name)
    else:
        # Display instructions when no data is processed
        st.info("Upload your financial documents using the sidebar and click 'Process Documents' to begin analysis.")
        
        # Display sample images or instructions
        st.markdown("""
        ### How to use this tool:
        
        1. **Upload Documents**: Start by uploading your current month actuals (required). For more comprehensive analysis, also upload prior month actuals, budget, and prior year actuals.
        
        2. **Process Documents**: Click the 'Process Documents' button to extract and analyze the financial data.
        
        3. **Review Results**: Examine the comparative analysis and AI-generated insights to understand your property's financial performance.
        
        4. **Export or Share**: Use Streamlit's built-in options to download charts or share insights with your team.
        """)

if __name__ == "__main__":
    main()
