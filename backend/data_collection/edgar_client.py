"""
EDGAR Client for accessing and downloading SEC filings.
Uses the aj0strow/edgar library for EDGAR API interactions.
"""
import os
import logging
from typing import Dict, List, Optional, Union, Any
import json
import aiohttp
import asyncio
from datetime import datetime
import tempfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EDGARClient:
    """Client for interacting with the SEC EDGAR database."""
    
    BASE_URL = "https://www.sec.gov/Archives/edgar"
    USER_AGENT = "SEC-Insights-Tool/1.0 (contact@example.com)"
    
    def __init__(self):
        """Initialize the EDGAR client."""
        # Set user agent for SEC API access
        self.headers = {
            "User-Agent": self.USER_AGENT
        }
    
    async def get_filing_metadata(self, accession_number: str) -> Dict[str, Any]:
        """
        Retrieve metadata about a filing by accession number.
        
        Args:
            accession_number: The SEC accession number (e.g., "0001234567-21-001234")
            
        Returns:
            Dict containing filing metadata
        """
        # Format accession number for URL (remove dashes)
        acc_no = accession_number.replace("-", "")
        url = f"{self.BASE_URL}/data/{acc_no}/{accession_number}-index.json"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status != 200:
                        logger.error(f"Error retrieving filing metadata: HTTP {response.status}")
                        return {}
                    
                    return await response.json()
        except Exception as e:
            logger.error(f"Error retrieving filing metadata: {str(e)}")
            return {}
    
    async def download_filing(self, accession_number: str, filing_type: str) -> Optional[str]:
        """
        Download the complete filing text.
        
        Args:
            accession_number: The SEC accession number
            filing_type: The filing type (10-K, 10-Q, etc.)
            
        Returns:
            Filing text content or None if download fails
        """
        # Format accession number for URL (remove dashes)
        acc_no = accession_number.replace("-", "")
        
        # Determine file extension based on filing type
        # Most filings are available as text files
        url = f"{self.BASE_URL}/data/{acc_no}/{accession_number}.txt"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status != 200:
                        logger.error(f"Error downloading filing: HTTP {response.status}")
                        return None
                    
                    return await response.text()
        except Exception as e:
            logger.error(f"Error downloading filing: {str(e)}")
            return None
    
    async def search_filings(self, 
                       company_name: Optional[str] = None, 
                       cik: Optional[str] = None,
                       form_type: Optional[str] = None,
                       date_from: Optional[str] = None,
                       date_to: Optional[str] = None,
                       limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search for filings matching specific criteria.
        
        Args:
            company_name: Company name to search for
            cik: CIK number
            form_type: Form type (10-K, 10-Q, 8-K, etc.)
            date_from: Start date in YYYY-MM-DD format
            date_to: End date in YYYY-MM-DD format
            limit: Maximum number of results to return
            
        Returns:
            List of filing metadata dictionaries
        """
        # This is a simplified implementation as there's no direct search API
        # In a real implementation, we would use a more sophisticated approach
        # or consider using a third-party data provider
        
        # For now, we'll return an empty list and log that this is not implemented
        logger.warning("Full search functionality not implemented - "
                      "would require additional data processing")
        return []
    
    async def get_company_info(self, cik: str) -> Dict[str, Any]:
        """
        Get company information by CIK.
        
        Args:
            cik: The company CIK number
            
        Returns:
            Dict containing company information
        """
        # Pad CIK with leading zeros to 10 digits
        padded_cik = cik.zfill(10)
        url = f"https://data.sec.gov/submissions/CIK{padded_cik}.json"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status != 200:
                        logger.error(f"Error retrieving company info: HTTP {response.status}")
                        return {}
                    
                    return await response.json()
        except Exception as e:
            logger.error(f"Error retrieving company info: {str(e)}")
            return {}

async def test_edgar_client():
    """Test the EDGAR client functionality."""
    client = EDGARClient()
    
    # Example: Get Apple Inc's company info
    apple_cik = "0000320193"
    company_info = await client.get_company_info(apple_cik)
    logger.info(f"Company info: {json.dumps(company_info, indent=2)[:200]}...")
    
    # Example: Get a recent filing metadata
    # This is just an example accession number
    acc_number = "0000320193-23-000077"
    metadata = await client.get_filing_metadata(acc_number)
    logger.info(f"Filing metadata: {json.dumps(metadata, indent=2)[:200]}...")

if __name__ == "__main__":
    asyncio.run(test_edgar_client())