import requests
import json
import logging
import time
import traceback
import streamlit as st
from typing import Dict, Any, Optional

from config import get_extraction_api_url, get_api_key
from utils.helpers import format_for_noi_comparison

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ai_extraction')

def extract_noi_data(file: Any, document_type_hint: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Extract DETAILED NOI data from a single file using the ENHANCED extraction API.

    Args:
        file: Uploaded file object (from Streamlit).
        document_type_hint: Optional hint from the UI (e.g., 'current_month_actuals').

    Returns:
        Extracted detailed data structure or None if extraction failed.
    """
    api_url = get_extraction_api_url() # Make sure this points to the enhanced API
    api_key = get_api_key()

    if not api_key or len(api_key) < 5:
         st.error("Extraction API Key is not configured correctly in settings.")
         logger.error("Missing or invalid extraction API key.")
         return None

    logger.info(f"Extracting detailed data from {file.name} using API: {api_url}")
    logger.info(f"Document type hint provided: {document_type_hint}")

    try:
        # Prepare form data
        files_payload = {"file": (file.name, file.getvalue(), file.type)}
        data_payload = {}
        if document_type_hint:
            data_payload['document_type'] = document_type_hint

        # Prepare headers
        headers = {
            "x-api-key": api_key,
            # Add Authorization header as well if your API prefers it
            # "Authorization": f"Bearer {api_key}"
        }

        # Initialize progress
        progress_bar = st.progress(0)
        status_text = st.empty()
        status_text.text(f"🚀 Sending {file.name} for detailed extraction...")

        # Send request to API
        with st.spinner(f"Extracting detailed data from {file.name}..."):
            progress_bar.progress(30)
            # Log request details for debugging
            logger.info(f"Sending POST to {api_url} with headers: {list(headers.keys())}, data_payload: {data_payload.keys()}")

            response = requests.post(
                api_url,
                files=files_payload,
                data=data_payload, # Send type hint as form data
                headers=headers,
                # params={"api_key": api_key}, # Avoid sending key in params if using headers
                timeout=120 # Increase timeout for potentially longer AI processing
            )
            progress_bar.progress(70)
            status_text.text("Processing API response...")

        progress_bar.progress(90)
        status_text.text("Finalizing extraction...")

        # Check if request was successful
        if response.status_code == 200:
            progress_bar.progress(100)
            status_text.success(f"✅ Detailed extraction complete for {file.name}!")
            time.sleep(1) # Allow user to see success message
            status_text.empty() # Clear status text
            progress_bar.empty() # Clear progress bar

            result = response.json()
            logger.info(f"Successfully extracted detailed data from {file.name}")
            # Log warnings from backend if present
            if 'validation_warnings' in result:
                 logger.warning(f"Backend validation warnings for {file.name}: {result['validation_warnings']}")
                 # Check if validation_warnings is an iterable before joining
                 if isinstance(result['validation_warnings'], list):
                     st.warning(f"Data validation warnings for {file.name}: {'; '.join(result['validation_warnings'])}")
                 else:
                     # Handle case where validation_warnings is not a list
                     st.warning(f"Data validation warnings for {file.name}: {result['validation_warnings']}")
            # logger.debug(f"Received data: {json.dumps(result, indent=2)}")
            return result
        else:
            logger.error(f"API error ({file.name}): {response.status_code} - {response.text}")
            try:
                 # Try to parse error detail from JSON response
                 error_detail = response.json().get("detail", response.text)
            except json.JSONDecodeError:
                 error_detail = response.text
            st.error(f"API Error ({response.status_code}) for {file.name}: {error_detail}")
            status_text.error(f"❌ Extraction failed for {file.name}.")
            progress_bar.empty()
            return None

    except requests.exceptions.Timeout:
        logger.error(f"Request timed out while processing {file.name}")
        st.error(f"Request timed out processing {file.name}. The server might be busy or the file too complex.")
        status_text.error(f"❌ Timeout during extraction for {file.name}.")
        if 'progress_bar' in locals(): progress_bar.empty()
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error. Could not connect to the extraction API at {api_url}")
        st.error(f"Connection Error: Could not connect to the API at {api_url}. Is the backend running?")
        status_text.error(f"❌ Connection error for {file.name}.")
        if 'progress_bar' in locals(): progress_bar.empty()
        return None
    except Exception as e:
        logger.error(f"Error extracting data ({file.name}): {str(e)}")
        logger.error(traceback.format_exc())
        st.error(f"An unexpected error occurred during extraction for {file.name}: {str(e)}")
        status_text.error(f"❌ Error during extraction for {file.name}.")
        if 'progress_bar' in locals(): progress_bar.empty()
        return None
