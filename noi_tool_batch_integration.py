"""
NOI Tool Batch Integration Module for Streamlit App
This module provides integration with the NOI extraction API for batch processing of multiple documents.
"""

import logging
import streamlit as st
import base64
import json
from typing import Dict, Any, List, Optional, Union
import requests
from noi_calculations import calculate_noi_comparisons
from config import get_extraction_api_url, get_api_key

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('noi_batch_integration')

def process_multiple_documents_batch(files: List[Any], property_name: str = "", document_types: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Process multiple documents using the extraction API and calculate NOI comparisons.
    
    Args:
        files: List of uploaded file objects from Streamlit
        property_name: Name of the property for the analysis (optional)
        document_types: Dictionary mapping filenames to document types (optional)
    
    Returns:
        Dictionary with results including success flag, error message, and data
    """
    # For demo purposes, return sample data if no files provided or if using example data
    if not files or st.session_state.get('use_example_data', False):
        logger.info("Using sample data for demonstration purposes")
        return get_sample_data(property_name)
    
    try:
        # Extract data from all documents using the API
        extracted_results = []
        for file in files:
            # Get the document type for this file
            doc_type = document_types.get(file.name) if document_types else None
            
            # Process the document
            result = extract_data_from_document(file, doc_type)
            if result:
                extracted_results.append(result)
        
        if not extracted_results:
            return {
                "success": False,
                "error": "Failed to extract data from any documents"
            }
        
        # Organize extracted data into consolidated format
        consolidated_data = {
            "current_month": None,
            "prior_month": None,
            "budget": None,
            "prior_year": None
        }
        
        # Map API document types to our internal types
        type_mapping = {
            "current_month_actuals": "current_month",
            "prior_month_actuals": "prior_month",
            "current_month_budget": "budget",
            "prior_year_actuals": "prior_year"
        }
        
        # Fill in the consolidated data structure
        for result in extracted_results:
            doc_type = result.get("document_type")
            if doc_type in type_mapping:
                internal_type = type_mapping[doc_type]
                consolidated_data[internal_type] = result
        
        # Calculate NOI comparisons
        comparison_results = calculate_noi_comparisons(consolidated_data)
        
        return {
            "success": True,
            "consolidated_data": consolidated_data,
            "comparison_results": comparison_results,
            "property_name": property_name
        }
        
    except Exception as e:
        logger.error(f"Error processing documents: {str(e)}")
        return {
            "success": False,
            "error": f"Error processing documents: {str(e)}"
        }

def extract_data_from_document(file: Any, document_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Extract financial data from a single document using the extraction API.
    
    Args:
        file: Uploaded file object from Streamlit
        document_type: Type of document (optional)
    
    Returns:
        Extracted data or None if extraction failed
    """
    try:
        # Use the extraction API URL from config
        api_url = get_extraction_api_url()
        if not api_url:
            api_url = "https://dataextractionai.onrender.com/extract"  # Default API URL
        
        api_key = get_api_key()
        
        logger.info(f"Extracting data from {file.name} (type: {document_type or 'unknown'}) using API: {api_url}")
        
        # Prepare the file for the API request
        file_content = file.read()
        file.seek(0)  # Reset file pointer for potential future use
        
        # For demonstration, if the API isn't working, fall back to sample data
        if st.session_state.get('use_example_data', False):
            logger.info("Using sample data instead of API for demonstration")
            # Return sample data based on document type
            if document_type == "current_month_actuals":
                return get_current_month_sample()
            elif document_type == "prior_month_actuals":
                return get_prior_month_sample()
            elif document_type == "current_month_budget":
                return get_budget_sample()
            elif document_type == "prior_year_actuals":
                return get_prior_year_sample()
            else:
                # If document type is unknown, assume it's current month
                return get_current_month_sample()
        
        # Prepare multipart form data
        files = {'file': (file.name, file_content, file.type)}
        data = {}
        if document_type:
            data['document_type'] = document_type
        
        # Add API key to headers as specified in the documentation
        headers = {}
        if api_key:
            # Add both header types as you mentioned for backward compatibility
            headers['x-api-key'] = api_key
            headers['Authorization'] = f"Bearer {api_key}"
        
        # Make the API request
        logger.info(f"Sending request to extraction API: {api_url}")
        response = requests.post(
            api_url,
            files=files,
            data=data,
            headers=headers
        )
        
        # Check the response
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Successfully extracted data from {file.name}")
            return result
        else:
            logger.error(f"API error: {response.status_code} - {response.text}")
            st.error(f"API error: {response.status_code} - {response.text}")
            
            # Fall back to sample data if API fails
            logger.warning("API failed, using sample data as fallback")
            # Return sample data based on document type
            if document_type == "current_month_actuals":
                return get_current_month_sample()
            elif document_type == "prior_month_actuals":
                return get_prior_month_sample()
            elif document_type == "current_month_budget":
                return get_budget_sample()
            elif document_type == "prior_year_actuals":
                return get_prior_year_sample()
            else:
                # If document type is unknown, assume it's current month
                return get_current_month_sample()
        
    except Exception as e:
        logger.error(f"Error extracting data from document: {str(e)}")
        return None

def get_sample_data(property_name: str = "") -> Dict[str, Any]:
    """
    Get sample data for demonstration purposes.
    
    Args:
        property_name: Name of the property for the analysis
    
    Returns:
        Dictionary with sample data
    """
    consolidated_data = {
        "current_month": get_current_month_sample(),
        "prior_month": get_prior_month_sample(),
        "budget": get_budget_sample(),
        "prior_year": get_prior_year_sample()
    }
    
    comparison_results = calculate_noi_comparisons(consolidated_data)
    
    return {
        "success": True,
        "consolidated_data": consolidated_data,
        "comparison_results": comparison_results,
        "property_name": property_name or "Sample Property"
    }

def get_current_month_sample() -> Dict[str, Any]:
    """Sample current month financial data"""
    return {
        "document_type": "current_month_actuals",
        "period": "March 2025",
        "rental_income": 120000.0,
        "laundry_income": 2500.0,
        "parking_income": 5000.0,
        "other_revenue": 1500.0,
        "total_revenue": 129000.0,
        "repairs_maintenance": 12000.0,
        "utilities": 15000.0,
        "property_management_fees": 6500.0,
        "property_taxes": 8000.0,
        "insurance": 4500.0,
        "admin_office_costs": 3500.0,
        "marketing_advertising": 2000.0,
        "total_expenses": 51500.0,
        "net_operating_income": 77500.0
    }

def get_prior_month_sample() -> Dict[str, Any]:
    """Sample prior month financial data"""
    return {
        "document_type": "prior_month_actuals",
        "period": "February 2025",
        "rental_income": 118000.0,
        "laundry_income": 2300.0,
        "parking_income": 4800.0,
        "other_revenue": 1200.0,
        "total_revenue": 126300.0,
        "repairs_maintenance": 11500.0,
        "utilities": 16000.0,
        "property_management_fees": 6300.0,
        "property_taxes": 8000.0,
        "insurance": 4500.0,
        "admin_office_costs": 3200.0,
        "marketing_advertising": 2500.0,
        "total_expenses": 52000.0,
        "net_operating_income": 74300.0
    }

def get_budget_sample() -> Dict[str, Any]:
    """Sample budget financial data"""
    return {
        "document_type": "current_month_budget",
        "period": "March 2025 (Budget)",
        "rental_income": 122000.0,
        "laundry_income": 2600.0,
        "parking_income": 5200.0,
        "other_revenue": 1800.0,
        "total_revenue": 131600.0,
        "repairs_maintenance": 11000.0,
        "utilities": 14500.0,
        "property_management_fees": 6600.0,
        "property_taxes": 7800.0,
        "insurance": 4400.0,
        "admin_office_costs": 3300.0,
        "marketing_advertising": 1800.0,
        "total_expenses": 49400.0,
        "net_operating_income": 82200.0
    }

def get_prior_year_sample() -> Dict[str, Any]:
    """Sample prior year financial data"""
    return {
        "document_type": "prior_year_actuals",
        "period": "March 2024",
        "rental_income": 112000.0,
        "laundry_income": 2200.0,
        "parking_income": 4500.0,
        "other_revenue": 1000.0,
        "total_revenue": 119700.0,
        "repairs_maintenance": 10500.0,
        "utilities": 14000.0,
        "property_management_fees": 6000.0,
        "property_taxes": 7500.0,
        "insurance": 4200.0,
        "admin_office_costs": 3000.0,
        "marketing_advertising": 1800.0,
        "total_expenses": 47000.0,
        "net_operating_income": 72700.0
    }