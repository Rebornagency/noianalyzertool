import os
import logging
from dotenv import load_dotenv
# Load environment variables from .env file if present
load_dotenv()
# OpenAI API key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "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") 
# Default extraction API URL - Make sure this points to your *enhanced* backend
DEFAULT_EXTRACTION_API_URL = os.environ.get("EXTRACTION_API_URL", "https://dataextractionai.onrender.com/extract") 
# Default API key for the extraction API - Make sure this matches your *enhanced* backend key
DEFAULT_API_KEY = os.environ.get("API_KEY", "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") 
def get_openai_api_key():
    return OPENAI_API_KEY
def get_extraction_api_url():
    return DEFAULT_EXTRACTION_API_URL
def get_api_key():
    return DEFAULT_API_KEY
