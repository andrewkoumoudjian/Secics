import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
import json
from datetime import datetime
import re

from .models import ModelClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FilingAnalyzer:
    """Analyzer for SEC filings using LLM models."""
    
    # Filing types that need special processing
    IMPORTANT_FILING_TYPES = {
        "10-K": "Annual report",
        "10-Q": "Quarterly report",
        "8-K": "Current report",
        "S-1": "IPO registration",
        "13F": "Institutional investment report",
        "4": "Insider trading report",
        "13D": "Beneficial ownership report",
        "13G": "Beneficial ownership report (passive)",
        "DEF 14A": "Proxy statement",
    }
    
    # Known sections of interest in different filing types
    SECTIONS_OF_INTEREST = {
        "10-K": [
            "Risk Factors",
            "Management's Discussion and Analysis",
            "Financial Statements",
            "Controls and Procedures",
            "Executive Compensation"
        ],
        "10-Q": [
            "Management's Discussion and Analysis",
            "Financial Statements", 
            "Controls and Procedures",
            "Risk Factors"
        ],
        "8-K": [
            "Item 1.01", "Item 1.02", "Item 2.01", "Item 2.02",
            "Item 4.01", "Item 5.01", "Item 5.02", "Item 8.01"
        ],
        "4": [
            "Table I", "Table II", "Remarks"
        ],
    }
    
    def __init__(self, model_client: Optional[ModelClient] = None):
        """
        Initialize the filing analyzer.
        
        Args:
            model_client: ModelClient instance for LLM interaction
        """
        self.model_client = model_client or ModelClient()
    
    def _extract_sections(self, filing_text: str, filing_type: str) -> Dict[str, str]:
        """
        Extract relevant sections from filing text based on filing type.
        
        Args:
            filing_text: The complete filing text
            filing_type: The type of filing
            
        Returns:
            Dict mapping section names to their contents
        """
        sections = {}
        
        # Get sections of interest for this filing type
        target_sections = self.SECTIONS_OF_INTEREST.get(filing_type, [])
        
        if not target_sections:
            # If no specific sections defined, return the whole filing
            return {"complete_filing": filing_text}
            
        # Simple section extraction based on section headers
        # In a real system, this would be more sophisticated with regex patterns
        for section in target_sections:
            pattern = re.compile(
                rf"(?i){re.escape(section)}[\s\n:.]*([^\n]+[\n].*?)(?=(?:{"|".join(map(re.escape, target_sections))})|$)", 
                re.DOTALL
            )
            matches = pattern.findall(filing_text)
            if matches:
                sections[section] = matches[0].strip()
            
        return sections
    
    async def _analyze_section(self, section_name: str, section_text: str, filing_type: str) -> Dict[str, Any]:
        """
        Analyze a specific section of a filing.
        
        Args:
            section_name: Name of the section
            section_text: Text content of the section
            filing_type: Type of the filing
            
        Returns:
            Dict containing analysis results for the section
        """
        # Create a section-specific prompt template
        prompt_template = f"""
        You are examining the '{section_name}' section of a {filing_type} SEC filing.
        
        Section content:
        {{text}}
        
        Analyze this section and provide:
        1. Key information and insights
        2. Any notable changes or unusual items
        3. Financial implications, if applicable
        4. Risks or red flags, if any
        5. A brief summary of the most important points
        
        Format your response as a concise analysis that could be presented to financial analysts.
        """
        
        # Truncate very long sections to fit model context
        max_length = 50000  # Adjust based on model token limits
        truncated_text = section_text[:max_length]
        if len(section_text) > max_length:
            truncated_text += "\n... [content truncated due to length]"
            
        # Call the model for analysis
        analysis_result = await self.model_client.analyze_text(
            text=truncated_text,
            task_type="analysis",
            prompt_template=prompt_template
        )
        
        return {
            "section_name": section_name,
            "analysis": analysis_result.get("analysis", ""),
            "success": analysis_result.get("success", False)
        }
    
    async def analyze_filing(self, 
                       filing_text: str, 
                       filing_metadata: Dict[str, Any],
                       company_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze a complete SEC filing.
        
        Args:
            filing_text: The complete filing text
            filing_metadata: Metadata about the filing
            company_info: Optional company information
            
        Returns:
            Dict containing complete analysis results
        """
        # Extract filing type from metadata
        filing_type = filing_metadata.get("form_type", "unknown")
        
        # Get filing date
        filing_date = filing_metadata.get("filing_date", datetime.now().strftime("%Y-%m-%d"))
        
        # Begin with overall filing summary
        summary_prompt = f"""
        This is a {filing_type} SEC filing from {filing_date}.
        
        {{text}}
        
        Provide a concise summary of this filing, highlighting:
        1. The main purpose and key information
        2. Financial highlights (if present)
        3. Important events or changes disclosed
        4. Any significant risks or concerns
        """
        
        # Get summary of the entire filing (using first part if too long)
        max_summary_length = 50000  # Character limit for summary
        summary_result = await self.model_client.analyze_text(
            text=filing_text[:max_summary_length],
            task_type="summarization",
            prompt_template=summary_prompt
        )
        
        # Extract relevant sections based on filing type
        sections = self._extract_sections(filing_text, filing_type)
        
        # Analyze each section in parallel
        section_analyses = []
        analysis_tasks = []
        
        for section_name, section_text in sections.items():
            if section_text:  # Only analyze non-empty sections
                task = self._analyze_section(section_name, section_text, filing_type)
                analysis_tasks.append(task)
        
        if analysis_tasks:
            section_analyses = await asyncio.gather(*analysis_tasks)
        
        # Generate overall assessment
        assessment_prompt = f"""
        You are a financial expert analyzing a {filing_type} SEC filing.
        
        Review this summary of the filing:
        {{text}}
        
        Based on this summary, provide:
        1. An overall assessment of the company's situation
        2. Key takeaways for investors
        3. Potential impact on the company's financial position
        4. Any significant events or changes worth monitoring
        5. A brief conclusion with an outlook
        """
        
        assessment_result = await self.model_client.analyze_text(
            text=summary_result.get("analysis", "No summary available"),
            task_type="analysis",
            prompt_template=assessment_prompt
        )
        
        # Compile results
        return {
            "filing_id": filing_metadata.get("accession_number", "unknown"),
            "company": {
                "name": filing_metadata.get("company_name", "unknown"),
                
