# NOI Tool - Enhanced for Detailed Analysis

This project provides a Streamlit application for analyzing Net Operating Income (NOI) from financial documents, providing detailed comparisons and AI-generated insights.

## Features

- Upload and process financial documents (PDF, Excel, CSV)
- Extract detailed financial data using an enhanced backend API
- Calculate comparisons based on GPR, EGI, Vacancy, OpEx
- Display detailed metrics and visualizations
- Generate AI-powered insights using GPT
- Compare current month data with prior month, budget, and prior year

## Installation

1. Clone the repository
2. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set your API keys as environment variables or in a `.env` file:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   EXTRACTION_API_URL=your_extraction_api_url_here
   API_KEY=your_extraction_api_key_here
   ```

## Usage

Run the Streamlit application:
```
streamlit run app.py
```

Or use the main entry point:
```
python main.py
```

The application will be available at http://localhost:8501

## Project Structure

- `app.py`: Main Streamlit application for NOI Analyzer
- `noi_calculations.py`: Calculates NOI comparisons based on consolidated data
- `config.py`: Configuration settings and API keys
- `noi_tool_batch_integration.py`: Handles batch processing of documents
- `ai_insights_gpt.py`: Generates insights using GPT
- `insights_display.py`: Displays insights in the Streamlit UI
- `ai_extraction.py`: Extracts financial data from documents
- `utils/helpers.py`: Utility functions for data formatting
- `main.py`: Entry point for running the application

## Dependencies

- streamlit==1.32.0
- pandas==2.1.4
- numpy==1.26.3
- requests==2.31.0
- plotly==5.18.0
- python-dotenv==1.0.0
- openai>=1.0.0

## License

This project is licensed under the MIT License - see the LICENSE file for details.
