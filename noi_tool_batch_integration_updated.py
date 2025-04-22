"""
Enhanced NOI Tool Batch Integration Module
This module is updated to work with the new clearly labeled document approach
and properly utilize document type information from the NOI Tool
"""

import streamlit as st
import requests
import json
from typing import Dict, Any, List, Union, Optional
import os
import logging
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from config import get_extraction_api_url, get_api_key

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('noi_tool_batch_integration')

def process_multiple_documents_batch(files: List[Any], property_name: str = "", document_types: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Process multiple documents using the batch API endpoint
    
    Args:
        files: List of uploaded files
        property_name: Name of the property for the analysis
        document_types: Dictionary mapping filenames to document types
        
    Returns:
        Dictionary with processed data and comparison results
    """
    logger.info(f"Processing {len(files)} documents using batch API")
    
    # Get API configuration
    API_URL = get_extraction_api_url()
    API_KEY = get_api_key()
    
    # Construct batch endpoint URL
    batch_url = API_URL
    if not batch_url.endswith('/extract-batch'):
        # If the URL ends with /extract, replace it with /extract-batch
        if batch_url.endswith('/extract'):
            batch_url = batch_url.replace('/extract', '/extract-batch')
        # Otherwise, append /extract-batch
        else:
            batch_url = f"{batch_url.rstrip('/')}/extract-batch"
    
    try:
        # Initialize progress indicators
        progress = st.progress(0)
        progress_text = st.empty()
        progress_text.text("Preparing files for batch extraction...")
        progress.progress(10)
        
        # Prepare headers with API key
        headers = {"x-api-key": API_KEY}
        
        # Prepare files for batch API request
        form_data = []
        for file in files:
            form_data.append(('files', (file.name, file.getvalue(), file.type)))
        
        # Add property name if provided
        if property_name:
            form_data.append(('property_name', property_name))
        
        # Add document types if provided
        if document_types:
            form_data.append(('document_types', json.dumps(document_types)))
        
        # Update progress
        progress_text.text("Sending files to extraction API...")
        progress.progress(30)
        
        # Send batch request to API
        with st.spinner(f"Processing {len(files)} files in batch mode..."):
            # Log the request details
            logger.info(f"Sending batch request to {batch_url}")
            logger.info(f"Document types: {document_types}")
            
            # Send request
            response = requests.post(
                batch_url,
                files=form_data,
                headers=headers,
                timeout=120  # Longer timeout for batch processing
            )
        
        # Update progress
        progress_text.text("Processing API response...")
        progress.progress(70)
        
        # Log the response for debugging
        logger.info(f"API Response Status: {response.status_code}")
        logger.info(f"API Response Headers: {response.headers}")
        
        # Check if request was successful
        if response.status_code == 200:
            try:
                # Complete progress
                progress.progress(100)
                progress_text.text("Batch extraction complete!")
                
                # Log the raw response text for debugging
                logger.info(f"API Response Text: {response.text[:500]}...")  # Log first 500 chars
                
                result = response.json()
                logger.info(f"Successfully processed {len(files)} documents")
                
                # Extract consolidated data
                consolidated_data = result.get("consolidated_data", {})
                
                # Log the consolidated data for debugging
                logger.info(f"Consolidated Data: {json.dumps(consolidated_data, default=str)[:500]}...")
                
                # Import the calculate_noi_comparisons function
                from noi_calculations import calculate_noi_comparisons
                
                # Calculate NOI comparisons
                try:
                    # Pass the consolidated data directly to the calculation function
                    comparison_results = calculate_noi_comparisons(consolidated_data)
                    
                    return {
                        "consolidated_data": consolidated_data,
                        "comparison_results": comparison_results,
                        "raw_results": result.get("results", []),
                        "success": True
                    }
                except Exception as e:
                    logger.error(f"Error calculating NOI comparisons: {str(e)}")
                    # Include traceback for better debugging
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    return {
                        "consolidated_data": consolidated_data,
                        "error": f"Error calculating comparisons: {str(e)}",
                        "raw_results": result.get("results", []),
                        "success": False
                    }
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON response: {str(e)}")
                logger.error(f"Response text: {response.text[:1000]}...")  # Log first 1000 chars
                return {
                    "error": f"Invalid JSON response from API: {str(e)}",
                    "success": False
                }
        else:
            logger.error(f"API error: {response.status_code} - {response.text}")
            # Try fallback to individual processing if batch fails
            logger.info("Attempting fallback to individual file processing")
            return fallback_to_individual_processing(files, property_name, document_types)
    except Exception as e:
        logger.error(f"Error processing documents: {str(e)}")
        # Include traceback for better debugging
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "error": str(e),
            "success": False
        }

def fallback_to_individual_processing(files: List, property_name: str = "", document_types: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Fallback to processing files individually if batch processing fails
    
    Args:
        files: List of uploaded files
        property_name: Name of the property for the analysis
        document_types: Dictionary mapping filenames to document types
        
    Returns:
        Dictionary with processing results
    """
    logger.info(f"Falling back to individual processing for {len(files)} files")
    
    # Get API configuration
    api_url = get_extraction_api_url()
    api_key = get_api_key()
    
    # Initialize consolidated data structure
    consolidated_data = {
        "current_month": None,
        "prior_month": None,
        "budget": None,
        "prior_year": None
    }
    
    # Track raw results
    raw_results = []
    
    # Process each file individually
    for file in files:
        try:
            # Create form data with file
            file_data = {"file": (file.name, file.getvalue(), file.type)}
            headers = {"x-api-key": api_key}
            
            # Add property name if provided
            params = {}
            if property_name:
                params["property_name"] = property_name
            
            # Add document type if provided
            if document_types and file.name in document_types:
                params["document_type"] = document_types[file.name]
                logger.info(f"Using provided document type for {file.name}: {document_types[file.name]}")
            
            # Send request to API
            with st.spinner(f"Processing {file.name} individually..."):
                response = requests.post(api_url, files=file_data, headers=headers, params=params, timeout=60)
            
            # Check if request was successful
            if response.status_code == 200:
                result = response.json()
                raw_results.append(result)
                
                # Determine document type based on provided mapping, file name, or content
                if document_types and file.name in document_types:
                    doc_type = map_document_type_to_internal(document_types[file.name])
                else:
                    doc_type = determine_document_type(file.name, result)
                
                # Format data for NOI comparison
                financials = result.get("financials", {})
                formatted_data = format_for_noi_comparison(financials)
                
                # Store in consolidated data based on document type
                if doc_type == "current_month" and consolidated_data["current_month"] is None:
                    consolidated_data["current_month"] = formatted_data
                    st.success(f"Processed {file.name} as current month data")
                elif doc_type == "prior_month" and consolidated_data["prior_month"] is None:
                    consolidated_data["prior_month"] = formatted_data
                    st.success(f"Processed {file.name} as prior month data")
                elif doc_type == "budget" and consolidated_data["budget"] is None:
                    consolidated_data["budget"] = formatted_data
                    st.success(f"Processed {file.name} as budget data")
                elif doc_type == "prior_year" and consolidated_data["prior_year"] is None:
                    consolidated_data["prior_year"] = formatted_data
                    st.success(f"Processed {file.name} as prior year data")
        except Exception as e:
            logger.error(f"Error processing {file.name} individually: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            st.warning(f"Could not process {file.name}: {str(e)}")
            # Continue processing other files even if one fails
            continue
    
    # Check if any files were successfully processed
    if any(consolidated_data.values()):
        # Calculate NOI comparisons
        from noi_calculations import calculate_noi_comparisons
        comparison_results = calculate_noi_comparisons(consolidated_data)
        
        return {
            "success": True,
            "consolidated_data": consolidated_data,
            "comparison_results": comparison_results,
            "raw_results": raw_results
        }
    else:
        return {
            "success": False,
            "error": "Failed to process any files individually"
        }

def format_for_noi_comparison(financials: Dict[str, Any]) -> Dict[str, float]:
    """
    Format financial data for NOI comparison
    
    Args:
        financials: Financial data from API response
        
    Returns:
        Formatted data with revenue, expenses, and NOI
    """
    # Extract the relevant values with defaults of 0 for missing values
    revenue = financials.get('total_revenue', 0)
    expenses = financials.get('total_expenses', 0)
    noi = financials.get('net_operating_income', 0)
    
    # If NOI is not provided but we have revenue and expenses, calculate it
    if noi == 0 and revenue != 0 and expenses != 0:
        noi = revenue - expenses
    
    # Format according to the expected structure
    formatted_data = {
        "revenue": revenue,
        "expense": expenses,  # Note: NOI calculations expects "expense" not "expenses"
        "noi": noi
    }
    
    return formatted_data

def map_document_type_to_internal(doc_type: str) -> str:
    """
    Map external document type to internal document type
    
    Args:
        doc_type: External document type
        
    Returns:
        Internal document type (current_month, prior_month, budget, prior_year)
    """
    doc_type = doc_type.lower()
    
    if doc_type in ["current_month_actuals", "current_month", "actuals"]:
        return "current_month"
    elif doc_type in ["prior_month_actuals", "prior_month", "previous_month"]:
        return "prior_month"
    elif doc_type in ["current_month_budget", "budget"]:
        return "budget"
    elif doc_type in ["prior_year_actuals", "prior_year", "previous_year"]:
        return "prior_year"
    else:
        # Default to current month if can't determine
        logger.warning(f"Unknown document type: {doc_type}, defaulting to current_month")
        return "current_month"

def determine_document_type(filename: str, result: Dict[str, Any]) -> str:
    """
    Determine document type based on filename or content
    
    Args:
        filename: Name of the file
        result: API response data
        
    Returns:
        Document type (current_month, prior_month, budget, prior_year)
    """
    # Check if API result contains document type
    if "document_type" in result:
        doc_type = result["document_type"].lower()
        if "actual" in doc_type or "income statement" in doc_type:
            # Check if it's prior year
            if "prior year" in doc_type or "previous year" in doc_type:
                return "prior_year"
            # Check if it's prior month
            elif "prior month" in doc_type or "previous month" in doc_type:
                return "prior_month"
            # Otherwise assume current month
            else:
                return "current_month"
        elif "budget" in doc_type:
            return "budget"
    
    # Otherwise, try to determine from filename
    filename = filename.lower()
    if "budget" in filename:
        return "budget"
    elif "prior year" in filename or "previous year" in filename:
        return "prior_year"
    elif "prior month" in filename or "previous month" in filename:
        return "prior_month"
    elif "current" in filename or "actual" in filename:
        return "current_month"
    
    # Default to current month if can't determine
    logger.warning(f"Could not determine document type for {filename}, defaulting to current_month")
    return "current_month"
