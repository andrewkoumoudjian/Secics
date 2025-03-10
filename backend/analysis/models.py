"""
Models module for integrating with OpenRouter LLM models.
Handles model selection, API interaction, and response parsing.
"""
import os
import logging
import json
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ModelClient:
    """Client for interacting with language models through OpenRouter."""
    
    # OpenRouter API base URL
    BASE_URL = "https://openrouter.ai/api/v1"
    
    # Default models to use
    DEFAULT_MODELS = {
        "default": "mistralai/mistral-7b-instruct:free",
        "analysis": "microsoft/phi-3-medium-128k-instruct:free",
        "summarization": "google/gemini-2.0-pro-exp-02-05:free",
        "classification": "mistralai/mistral-7b-instruct:free"
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the model client.
        
        Args:
            api_key: OpenRouter API key. If None, reads from OPENROUTER_API_KEY env var.
        """
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            logger.warning("No OpenRouter API key provided. Using demo mode with limited functionality.")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}" if self.api_key else "",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://sec-insights.example.com",  # Your site URL
            "X-Title": "SEC Insights Tool"  # Your site name
        }
    
    async def analyze_text(self, 
                     text: str, 
                     task_type: str = "default",
                     prompt_template: Optional[str] = None,
                     model: Optional[str] = None,
                     max_tokens: int = 1024) -> Dict[str, Any]:
        """
        Analyze text using the specified language model.
        
        Args:
            text: The text to analyze
            task_type: The type of analysis (default, analysis, summarization, classification)
            prompt_template: Optional prompt template to use (if None, uses a default template)
            model: Specific model to use (if None, uses the default for the task type)
            max_tokens: Maximum tokens to generate in response
            
        Returns:
            Dict containing analysis results
        """
        # Select model based on task type if not specified
        model_name = model or self.DEFAULT_MODELS.get(task_type, self.DEFAULT_MODELS["default"])
        
        # Create default prompt template based on task type
        if not prompt_template:
            if task_type == "summarization":
                prompt_template = "Summarize the following SEC filing text concisely:\n\n{text}"
            elif task_type == "analysis":
                prompt_template = """
                You are an expert financial analyst. Analyze the following SEC filing:
                
                {text}
                
                Provide insights on:
                1. Key financial highlights
                2. Important disclosures
                3. Changes from previous filings
                4. Potential red flags or notable items
                5. Overall assessment
                """
            elif task_type == "classification":
                prompt_template = """
                Classify the following SEC filing text:
                
                {text}
                
                Specify:
                - Type of event described
                - Sentiment (positive, negative, neutral)
                - Entities involved
                - Financial impact severity (high, medium, low, unknown)
                - Other relevant classifications
                """
            else:
                prompt_template = "Analyze the following SEC filing text:\n\n{text}"
        
        # Format the prompt with the provided text
        formatted_prompt = prompt_template.format(text=text[:100000])  # Limit text to avoid token overflow
        
        # Prepare request data
        data = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "You are a financial expert analyzing SEC filings."},
                {"role": "user", "content": formatted_prompt}
            ],
            "max_tokens": max_tokens
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.BASE_URL}/chat/completions", 
                    headers=self.headers,
                    json=data
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error calling model API: HTTP {response.status} - {error_text}")
                        return {
                            "success": False,
                            "error": f"API error: {response.status}",
                            "details": error_text
                        }
                    
                    result = await response.json()
                    
                    # Extract the actual response text
                    response_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    
                    return {
                        "success": True,
                        "model_used": model_name,
                        "task_type": task_type,
                        "analysis": response_text,
                        "raw_response": result
                    }
        except Exception as e:
            logger.error(f"Error processing analysis request: {str(e)}")
            return {
                "success": False,
                "error": "Processing error",
                "details": str(e)
            }

async def test_model_client():
    """Test the model client functionality."""
    client = ModelClient()
    
    # Example filing text (shortened for demonstration)
    test_text = """
    APPLE INC.
    FORM 8-K
    CURRENT REPORT
    Pursuant to Section 13 or 15(d) of The Securities Exchange Act of 1934
    
    Item 2.02 Results of Operations and Financial Condition.
    
    On January 27, 2022, Apple Inc. ("Apple") issued a press release regarding Apple's financial results for its first fiscal quarter ended December 25, 2021. A copy of Apple's press release is attached hereto as Exhibit 99.1.
    
    The information contained in this Current Report on Form 8-K, including the exhibit hereto, shall not be deemed "filed" for purposes of Section 18 of the Securities Exchange Act of 1934, as amended (the "Exchange Act"), or incorporated by reference in any filing under the Securities Act of 1933, as amended, or the Exchange Act, except as shall be expressly set forth by specific reference in such a filing.
    """
    
    # Test summarization
    summary_result = await client.analyze_text(test_text, task_type="summarization")
    logger.info(f"Summary: {summary_result.get('analysis')}")
    
    # Test analysis
    analysis_result = await client.analyze_text(test_text, task_type="analysis")
    logger.info(f"Analysis: {analysis_result.get('analysis')}")

if __name__ == "__main__":
    asyncio.run(test_model_client())
