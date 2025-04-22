import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file (if it exists)
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('config')

def get_openai_api_key():
    """
    Get the OpenAI API key from environment variables
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OpenAI API key not found in environment variables. "
                      "AI-powered insights will not be available.")
    return api_key

def get_extraction_api_url():
    """
    Get the extraction API URL from environment variables or use the default
    """
    api_url = os.getenv("EXTRACTION_API_URL", "https://dataextractionai.onrender.com/extract")
    return api_url

def get_api_key():
    """
    Get the API key for the extraction API from environment variables or use the default
    """
    api_key = os.getenv("API_KEY", "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")
    return api_key