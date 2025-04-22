"""
Enhanced Document Classifier Module for NOI Analyzer
This module is updated to work with the new clearly labeled document approach
and properly handle document types from the NOI Tool
"""

import os
import logging
import json
import re
from typing import Dict, Any, List, Tuple, Optional, Union
from openai import OpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('document_classifier')

class DocumentClassifier:
    """
    Class for classifying financial documents and extracting time periods
    using GPT-4, enhanced to work with labeled document types
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the document classifier
        
        Args:
            api_key: OpenAI API key (optional, can be set via environment variable)
        """
        # Set API key if provided, otherwise use environment variable
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = os.environ.get("OPENAI_API_KEY")
            
        if not self.api_key:
            logger.warning("OpenAI API key not set. Please set OPENAI_API_KEY environment variable or provide it during initialization.")
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key)
        
        # Document types we can classify
        self.document_types = [
            "Actual Income Statement",
            "Budget",
            "Prior Year Actual",
            "Unknown"
        ]
        
        # Mapping from NOI Tool document types to extraction tool document types
        self.document_type_mapping = {
            "current_month_actuals": "Actual Income Statement",
            "prior_month_actuals": "Actual Income Statement",
            "current_month_budget": "Budget",
            "prior_year_actuals": "Prior Year Actual"
        }
    
    def classify(self, text_or_data: Union[str, Dict[str, Any]], known_document_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Classify document type and extract time period, with option to use known document type
        
        Args:
            text_or_data: Preprocessed text from the document or data dictionary
            known_document_type: Known document type from labeled upload (optional)
            
        Returns:
            Dict containing document type and period
        """
        logger.info("Classifying document and extracting time period")
        
        # If known document type is provided, use it directly
        if known_document_type:
            logger.info(f"Using known document type: {known_document_type}")
            # Map the NOI Tool document type to extraction tool document type
            if known_document_type in self.document_type_mapping:
                doc_type = self.document_type_mapping[known_document_type]
                logger.info(f"Mapped known document type '{known_document_type}' to '{doc_type}'")
                
                # Extract period from the document content
                period = self._extract_period_from_content(text_or_data)
                
                return {
                    'document_type': doc_type,
                    'period': period,
                    'method': 'known_type'
                }
            else:
                logger.warning(f"Unknown document type mapping for '{known_document_type}', falling back to extraction")
        
        # Extract text from the input for period extraction
        extracted_text = self._extract_text_from_input(text_or_data)
        
        # Try to extract period from filename if it's in the data
        filename = None
        if isinstance(text_or_data, dict) and 'metadata' in text_or_data and 'filename' in text_or_data['metadata']:
            filename = text_or_data['metadata']['filename']
            logger.info(f"Found filename in metadata: {filename}")
        
        # Try to determine document type from filename
        doc_type_from_filename = self._determine_type_from_filename(filename) if filename else None
        if doc_type_from_filename:
            logger.info(f"Determined document type from filename: {doc_type_from_filename}")
            period = self._extract_period_from_content(extracted_text) or self._extract_period_from_filename(filename)
            return {
                'document_type': doc_type_from_filename,
                'period': period,
                'method': 'filename'
            }
        
        # First try rule-based classification for efficiency
        rule_based_result = self._rule_based_classification(extracted_text)
        
        # If rule-based classification is confident, return the result
        if rule_based_result.get('confidence', 0) > 0.7:
            logger.info(f"Rule-based classification successful: {rule_based_result}")
            return {
                'document_type': rule_based_result['document_type'],
                'period': rule_based_result['period'],
                'method': 'rule_based'
            }
        
        # Otherwise, use GPT for classification
        gpt_result = self._gpt_classification(extracted_text)
        logger.info(f"GPT classification result: {gpt_result}")
        
        return {
            'document_type': gpt_result['document_type'],
            'period': gpt_result['period'],
            'method': 'gpt'
        }
    
    def _extract_text_from_input(self, text_or_data: Union[str, Dict[str, Any]]) -> str:
        """
        Extract text content from input which could be string or dictionary
        
        Args:
            text_or_data: Input data which could be string or dictionary
            
        Returns:
            Extracted text content
        """
        # Handle both string and dictionary input
        if isinstance(text_or_data, dict):
            # Extract text from dictionary if it's a dictionary
            logger.info("Input is a dictionary, extracting text content")
            
            # Try to extract text from common dictionary structures
            if 'combined_text' in text_or_data:
                return text_or_data['combined_text']
            elif 'text' in text_or_data:
                if isinstance(text_or_data['text'], str):
                    return text_or_data['text']
                elif isinstance(text_or_data['text'], list) and len(text_or_data['text']) > 0:
                    # Join text from multiple pages
                    return "\n\n".join([page.get('content', '') for page in text_or_data['text'] if isinstance(page, dict) and 'content' in page])
            elif 'content' in text_or_data:
                return text_or_data['content']
            elif 'data' in text_or_data and isinstance(text_or_data['data'], str):
                return text_or_data['data']
            elif 'sheets' in text_or_data and isinstance(text_or_data['sheets'], list):
                # Extract text from Excel sheets
                sheet_texts = []
                for sheet in text_or_data['sheets']:
                    if isinstance(sheet, dict) and 'name' in sheet and 'data' in sheet:
                        sheet_texts.append(f"Sheet: {sheet['name']}")
                        if isinstance(sheet['data'], list):
                            for row in sheet['data']:
                                if isinstance(row, dict):
                                    sheet_texts.append(str(row))
                return "\n".join(sheet_texts)
            
            # If we couldn't extract text using known structures, convert the entire dictionary to a string
            logger.warning("Could not find text field in dictionary, using JSON string representation")
            try:
                return json.dumps(text_or_data)
            except:
                return str(text_or_data)
        else:
            # Use the input directly if it's already a string
            if isinstance(text_or_data, str):
                return text_or_data
            else:
                # Convert to string if it's not a string
                logger.warning(f"Converted non-string input to string: {type(text_or_data)}")
                return str(text_or_data)
    
    def _extract_period_from_content(self, text_or_data: Union[str, Dict[str, Any]]) -> Optional[str]:
        """
        Extract period information from document content
        
        Args:
            text_or_data: Preprocessed text from the document or data dictionary
            
        Returns:
            Extracted period or None if not found
        """
        # Extract text from input
        text = self._extract_text_from_input(text_or_data)
        
        # Pattern for month and year (e.g., "March 2025", "Jan 2025", "January 2025")
        month_year_pattern = r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[,\s]+\d{4}'
        
        # Pattern for quarter (e.g., "Q1 2025", "First Quarter 2025")
        quarter_pattern = r'(?:Q[1-4]|(?:First|Second|Third|Fourth)\s+Quarter)[,\s]+\d{4}'
        
        # Pattern for year only (e.g., "2025", "FY 2025")
        year_pattern = r'(?:FY\s+)?\d{4}'
        
        # Try to find month and year
        month_year_match = re.search(month_year_pattern, text, re.IGNORECASE)
        if month_year_match:
            return month_year_match.group(0).strip()
            
        # Try to find quarter
        quarter_match = re.search(quarter_pattern, text, re.IGNORECASE)
        if quarter_match:
            return quarter_match.group(0).strip()
            
        # Try to find year only
        year_match = re.search(year_pattern, text)
        if year_match:
            return year_match.group(0).strip()
            
        return None
    
    def _determine_type_from_filename(self, filename: Optional[str]) -> Optional[str]:
        """
        Determine document type from filename
        
        Args:
            filename: Original filename
            
        Returns:
            Document type or None if can't determine
        """
        if not filename:
            return None
        
        filename_lower = filename.lower()
        
        # Check for document type indicators in filename
        if 'actual' in filename_lower:
            if 'prior' in filename_lower or 'previous' in filename_lower or 'last' in filename_lower:
                if 'year' in filename_lower:
                    return "Prior Year Actual"
                else:
                    return "Actual Income Statement"  # Assume prior month actual
            else:
                return "Actual Income Statement"  # Assume current month actual
        elif 'budget' in filename_lower:
            return "Budget"
        
        return None
    
    def _extract_period_from_filename(self, filename: str) -> str:
        """
        Extract period information from filename
        
        Args:
            filename: Original filename
            
        Returns:
            Extracted period or "Unknown Period" if not found
        """
        if not filename:
            return "Unknown Period"
            
        # Remove file extension
        filename_parts = os.path.splitext(filename)[0].split('_')
        
        # Define month abbreviations and pattern for year
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        year_pattern = r'20\d{2}'
        
        month = None
        year = None
        
        for part in filename_parts:
            # Check for month
            for m in months:
                if m.lower() in part.lower():
                    month = m
                    break
            
            # Check for year (2020-2099)
            year_match = re.search(year_pattern, part)
            if year_match:
                year = year_match.group(0)
        
        # Construct period string
        if month and year:
            return f"{month} {year}"
        elif year:
            return year
                
        return "Unknown Period"
    
    def _rule_based_classification(self, text: str) -> Dict[str, Any]:
        """
        Attempt to classify document using rule-based approach
        
        Args:
            text: Preprocessed text from the document
            
        Returns:
            Dict containing document type, period, and confidence
        """
        result = {
            'document_type': 'Unknown',
            'period': None,
            'confidence': 0.0
        }
        
        # Convert to lowercase for case-insensitive matching
        text_lower = text.lower()
        
        # Check for document type indicators
        if 'actual' in text_lower and ('income statement' in text_lower or 'statement of income' in text_lower):
            result['document_type'] = 'Actual Income Statement'
            result['confidence'] = 0.8
        elif 'budget' in text_lower:
            result['document_type'] = 'Budget'
            result['confidence'] = 0.8
        elif 'prior year' in text_lower or 'previous year' in text_lower:
            result['document_type'] = 'Prior Year Actual'
            result['confidence'] = 0.8
            
        # Extract period using regex patterns
        # Pattern for month and year (e.g., "March 2025", "Jan 2025", "January 2025")
        month_year_pattern = r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[,\s]+\d{4}'
        
        # Pattern for quarter (e.g., "Q1 2025", "First Quarter 2025")
        quarter_pattern = r'(?:Q[1-4]|(?:First|Second|Third|Fourth)\s+Quarter)[,\s]+\d{4}'
        
        # Pattern for year only (e.g., "2025", "FY 2025")
        year_pattern = r'(?:FY\s+)?\d{4}'
        
        # Try to find month and year
        month_year_match = re.search(month_year_pattern, text, re.IGNORECASE)
        if month_year_match:
            result['period'] = month_year_match.group(0).strip()
            result['confidence'] += 0.1
            
        # Try to find quarter
        quarter_match = re.search(quarter_pattern, text, re.IGNORECASE)
        if quarter_match:
            result['period'] = quarter_match.group(0).strip()
            result['confidence'] += 0.1
            
        # Try to find year only
        year_match = re.search(year_pattern, text)
        if year_match:
            result['period'] = year_match.group(0).strip()
            result['confidence'] += 0.05
            
        return result
    
    def _gpt_classification(self, text: str) -> Dict[str, Any]:
        """
        Classify document using GPT-4
        
        Args:
            text: Preprocessed text from the document
            
        Returns:
            Dict containing document type and period
        """
        # Prepare a sample of the text for GPT (first 1500 characters)
        text_sample = text[:1500]
        
        # Create the prompt for GPT
        prompt = f"""Classify this financial document as one of:
- Actual Income Statement
- Budget
- Prior Year Actual
- Unknown

Then extract the month and year or fiscal period.

Text sample:
{text_sample}

Respond in JSON format with document_type and period fields.
"""
        
        try:
            # Call OpenAI API with updated client format
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a senior real estate accountant specializing in financial document classification."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for more deterministic results
                max_tokens=150
            )
            
            # Extract response text
            response_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                result = json.loads(response_text)
                logger.info("Successfully parsed JSON response")
                
                # Ensure required fields are present
                if 'document_type' not in result:
                    result['document_type'] = 'Unknown'
                if 'period' not in result:
                    result['period'] = None
                    
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON response: {str(e)}")
                logger.error(f"Response text: {response_text}")
                
                # Try to extract document type and period using regex
                doc_type_match = re.search(r'(Actual Income Statement|Budget|Prior Year Actual|Unknown)', response_text)
                period_match = re.search(r'(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[,\s]+\d{4}', response_text)
                
                doc_type = doc_type_match.group(0) if doc_type_match else 'Unknown'
                period = period_match.group(0) if period_match else None
                
                return {
                    'document_type': doc_type,
                    'period': period
                }
                
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            return {
                'document_type': 'Unknown',
                'period': None
            }


def classify_document(text_or_data: Union[str, Dict[str, Any]], known_document_type: Optional[str] = None) -> Tuple[str, Optional[str]]:
    """
    Convenience function to classify a document and extract its period
    
    Args:
        text_or_data: Preprocessed text from the document or data dictionary
        known_document_type: Known document type from labeled upload (optional)
        
    Returns:
        Tuple containing document type and period
    """
    classifier = DocumentClassifier()
    result = classifier.classify(text_or_data, known_document_type)
    
    return result['document_type'], result['period']


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python document_classifier.py <file_path> [known_document_type]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    known_document_type = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        with open(file_path, 'r') as f:
            text = f.read()
        
        doc_type, period = classify_document(text, known_document_type)
        
        print(f"Document Type: {doc_type}")
        print(f"Period: {period}")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
