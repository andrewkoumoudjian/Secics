"""
Event Detector for identifying significant events in SEC filings.
Detects important events, categorizes them, and assigns risk/impact levels.
"""
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
import json
from datetime import datetime, timedelta
import re

from .models import ModelClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EventDetector:
    """Detects significant events in SEC filings."""
    
    # Event categories
    EVENT_CATEGORIES = [
        "Management Change",
        "Acquisition/Merger",
        "Divestiture",
        "Financial Results",
        "Regulatory Issue",
        "Legal Settlement",
        "Stock Buyback",
        "Dividend Announcement",
        "Default/Bankruptcy",
        "Strategic Partnership",
        "Product Launch",
        "Restructuring",
        "Insider Trading",
        "Accounting Change",
        "Other Material Event"
    ]
    
    # Form types and their typical events
    FORM_EVENT_MAPPING = {
        "8-K": [
            "Management Change",
            "Acquisition/Merger",
            "Financial Results",
            "Legal Settlement",
            "Default/Bankruptcy"
        ],
        "10-Q": [
            "Financial Results",
            "Regulatory Issue",
            "Legal Settlement"
        ],
        "10-K": [
            "Financial Results",
            "Risk Factors Update",
            "Accounting Change"
        ],
        "4": [
            "Insider Trading"
        ],
        "13D": [
            "Significant Ownership Change"
        ]
    }
    
    def __init__(self, model_client: Optional[ModelClient] = None):
        """
        Initialize the event detector.
        
        Args:
            model_client: ModelClient instance for LLM interaction
        """
        self.model_client = model_client or ModelClient()
    
    async def detect_events(self, 
                      filing_text: str, 
                      filing_metadata: Dict[str, Any],
                      filing_analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Detect significant events in a filing.
        
        Args:
            filing_text: The filing text content
            filing_metadata: Metadata about the filing
            filing_analysis: Optional pre-existing analysis of the filing
            
        Returns:
            Dict containing detected events and their details
        """
        # Get filing type and typical events for this form
        filing_type = filing_metadata.get("form_type", "unknown")
        typical_events = self.FORM_EVENT_MAPPING.get(filing_type, [])
        
        # If we have pre-existing analysis, use it to inform event detection
        analysis_context = ""
        if filing_analysis and filing_analysis.get("summary"):
            analysis_context = f"""
            Filing Summary:
            {filing_analysis.get('summary')}
            
            Overall Assessment:
            {filing_analysis.get('overall_assessment', '')}
            """
        
        # Create prompt for event detection
        event_categories_str = ", ".join(self.EVENT_CATEGORIES)
        typical_events_str = ", ".join(typical_events) if typical_events else "various events"
        
        prompt_template = f"""
        Analyze this {filing_type} SEC filing to identify significant events:
        
        {{text}}
        
        {analysis_context}
        
        Filing Type: {filing_type} (typically contains {typical_events_str})
        
        Possible event categories: {event_categories_str}
        
        For each significant event detected:
        1. Event category (from the list above)
        2. Brief description of the event
        3. Entities involved
        4. Financial impact assessment (None, Low, Medium, High, Unknown)
        5. Market impact potential (None, Low, Medium, High, Unknown)
        6. Risk level (Low, Medium, High, Critical)
        
        Format your response as a structured list of events with their attributes.
        If no significant events are detected, explicitly state so.
        """
        
        # Limit text length for model processing
        max_text_length = 25000
        truncated_text = filing_text[:max_text_length]
        
        # Call the model for event detection
        result = await self.model_client.analyze_text(
            text=truncated_text,
            task_type="analysis",
            prompt_template=prompt_template
        )
        
        # Parse the model response to extract events
        detected_events = self._parse_events(result.get("analysis", ""))
        
        return {
            "filing_id": filing_metadata.get("accession_number", "unknown"),
            "company_name": filing_metadata.get("company_name", "unknown"),
            "cik": filing_metadata.get("cik", "unknown"),
            "filing_type": filing_type,
            "filing_date": filing_metadata.get("filing_date", datetime.now().strftime("%Y-%m-%d")),
            "events": detected_events,
            "event_count": len(detected_events),
            "detection_timestamp": datetime.now().isoformat(),
            "has_critical_events": any(e.get("risk_level") == "Critical" for e in detected_events),
            "has_high_impact_events": any(e.get("market_impact") == "High" for e in detected_events)
        }
    
    def _parse_events(self, detection_text: str) -> List[Dict[str, Any]]:
        """
        Parse detected events from model output.
        
        Args:
            detection_text: The text output from the model
            
        Returns:
            List of event dictionaries
        """
        events = []
        
        # Check for "no events" indication
        if re.search(r'no significant events|no events detected', detection_text, re.IGNORECASE):
            return events
        
        # This is a simplified parser - in production, we would use
        # a more robust approach with better structure detection
        
        # Split by numbered items or sections
        event_blocks = re.split(r'\n\s*(?:\d+\.|\*|\-)\s*', detection_text)
        
        for block in event_blocks:
            block = block.strip()
            if not block or len(block) < 20:  # Skip empty or very short blocks
                continue
                
            event = {
                "description": block,
                "category": "Other Material Event",
                "entities_involved": [],
                "financial_impact": "Unknown",
                "market_impact": "Unknown",
                "risk_level": "Medium"
            }
            
            # Try to extract event category
            for category in self.EVENT_CATEGORIES:
                if re.search(rf'\b{re.escape(category)}\b', block, re.IGNORECASE):
                    event["category"] = category
                    break
            
            # Try to extract entities involved
            entities = re.findall(r'(?:entity|entities|company|person|organization)[^\w]*:?\s*([^,\n]+)', block, re.IGNORECASE)
            if entities:
                event["entities_involved"] = [e.strip() for e in entities]
            
            # Try to extract financial impact
            fin_match = re.search(r'financial impact[^\w]*:?\s*(\w+)', block, re.IGNORECASE)
            if fin_match:
                event["financial_impact"] = fin_match.group(1).capitalize()
            
            # Try to extract market impact
            market_match = re.search(r'market impact[^\w]*:?\s*(\w+)', block, re.IGNORECASE)
            if market_match:
                event["market_impact"] = market_match.group(1).capitalize()
            
            # Try to extract risk level
            risk_match = re.search(r'risk level[^\w]*:?\s*(\w+)', block, re.IGNORECASE)
            if risk_match:
                event["risk_level"] = risk_match.group(1).capitalize()
                
            events.append(event)
        
        return events

async def test_event_detector():
    """Test the event detector functionality."""
    detector = EventDetector()
    
    # Example filing text and metadata
    sample_filing = """
    UNITED STATES
    SECURITIES AND EXCHANGE COMMISSION
    Washington, D.C. 20549
    
    FORM 8-K
    
    CURRENT REPORT
    Pursuant to Section 13 or 15(d) of The Securities Exchange Act of 1934
    
    Date of Report (Date of earliest event reported): March 1, 2023
    
    APPLE INC.
    (Exact name of Registrant as specified in its charter)
    
    Item 5.02 Departure of Directors or Certain Officers; Election of Directors; 
    Appointment of Certain Officers; Compensatory Arrangements of Certain Officers.
    
    On February 28, 2023, Apple Inc. ("Apple") announced that Katherine Adams, Senior Vice President, 
    General Counsel and Secretary, will be stepping down from her role effective March 31, 2023. 
    Ms. Adams will be succeeded by Kate Andrias, who will join Apple from Columbia Law School, 
    where she has been a professor since 2021.
    """
    
    sample_metadata = {
        "accession_number": "0000320193-23-000022",
        "company_name": "APPLE INC",
        "cik": "0000320193",
        "form_type": "8-K",
        "filing_date": "2023-03-01"
    }
    
    # Detect events
    events_result = await detector.detect_events(sample_filing, sample_metadata)
    
    print(f"Detected events: {json.dumps(events_result.get('events', []), indent=2)}")
    print(f"Has critical events: {events_result.get('has_critical_events')}")

if __name__ == "__main__":
    asyncio.run(test_event_detector())