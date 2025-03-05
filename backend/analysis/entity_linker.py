"""
Entity Linker for connecting related SEC filings and detecting relationships.
Maps entities across filings and identifies relevant connections.
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

class EntityLinker:
    """Links related entities and detects connections across filings."""
    
    def __init__(self, model_client: Optional[ModelClient] = None):
        """
        Initialize the entity linker.
        
        Args:
            model_client: ModelClient instance for LLM interaction
        """
        self.model_client = model_client or ModelClient()
        self.entity_cache = {}  # Cache of previously identified entities
    
    async def extract_entities(self, filing_text: str, filing_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract named entities from a filing.
        
        Args:
            filing_text: The filing text content
            filing_metadata: Metadata about the filing
            
        Returns:
            Dict containing extracted entities and their context
        """
        # Create a prompt for entity extraction
        prompt_template = """
        Extract all important named entities from this SEC filing text:
        
        {text}
        
        For each entity, include:
        1. Entity name (company, person, organization)
        2. Entity type (company, person, organization, location, etc.)
        3. Role in the context (e.g., filer, acquirer, subsidiary, executive, etc.)
        4. Brief context about their mention
        
        Format your response as a structured list of entities with their attributes.
        """
        
        # Limit text length for model processing
        max_text_length = 25000
        truncated_text = filing_text[:max_text_length]
        
        # Call the model for entity extraction
        result = await self.model_client.analyze_text(
            text=truncated_text,
            task_type="analysis",
            prompt_template=prompt_template
        )
        
        # Parse the model response to extract entity information
        # This is a simplified implementation - in a real system,
        # we'd use more robust parsing techniques
        
        filing_id = filing_metadata.get("accession_number", "unknown")
        filing_date = filing_metadata.get("filing_date", datetime.now().strftime("%Y-%m-%d"))
        filing_type = filing_metadata.get("form_type", "unknown")
        
        return {
            "filing_id": filing_id,
            "filing_type": filing_type,
            "filing_date": filing_date,
            "company_name": filing_metadata.get("company_name", "unknown"),
            "cik": filing_metadata.get("cik", "unknown"),
            "extracted_text": result.get("analysis", ""),
            "raw_entities": self._parse_entities(result.get("analysis", "")),
            "extraction_timestamp": datetime.now().isoformat()
        }
    
    def _parse_entities(self, extraction_text: str) -> List[Dict[str, str]]:
        """
        Parse entity extraction results from model output.
        
        Args:
            extraction_text: The text output from the model
            
        Returns:
            List of entity dictionaries
        """
        entities = []
        
        # This is a simplified parser - in production, we would use
        # a more robust approach with better structure detection
        
        # Split by numbered lines or bullet points
        entity_blocks = re.split(r'\n\s*(?:\d+\.|\*|\-)\s*', extraction_text)
        
        for block in entity_blocks:
            block = block.strip()
            if not block:
                continue
                
            entity = {}
            
            # Look for entity name
            name_match = re.search(r'(?:entity|name|company|person):\s*([^,\n]+)', block, re.IGNORECASE)
            if name_match:
                entity["name"] = name_match.group(1).strip()
            else:
                # If no explicit name found, use first line or first few words
                lines = block.split('\n')
                entity["name"] = lines[0].strip()[:50]
            
            # Look for entity type
            type_match = re.search(r'(?:type|category):\s*([^,\n]+)', block, re.IGNORECASE)
            if type_match:
                entity["type"] = type_match.group(1).strip()
            else:
                entity["type"] = "unknown"
            
            # Look for entity role
            role_match = re.search(r'(?:role|function|position):\s*([^,\n]+)', block, re.IGNORECASE)
            if role_match:
                entity["role"] = role_match.group(1).strip()
            else:
                entity["role"] = "mentioned"
            
            # Add the context
            entity["context"] = block
            
            entities.append(entity)
        
        return entities
    
    async def link_entities(self, 
                      current_entities: Dict[str, Any], 
                      historical_entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Find connections between current filing entities and historical entities.
        
        Args:
            current_entities: Entity data from current filing
            historical_entities: List of entity data from previous filings
            
        Returns:
            Dict containing linked entities and relationship information
        """
        if not historical_entities:
            return {
                "filing_id": current_entities.get("filing_id", "unknown"),
                "links": [],
                "new_entities": current_entities.get("raw_entities", []),
                "link_timestamp": datetime.now().isoformat()
            }
        
        # Create a context string with historical entities
        historical_context = "\n\n".join([
            f"Filing ID: {h.get('filing_id')}, Date: {h.get('filing_date')}, Type: {h.get('filing_type')}\n"
            f"Company: {h.get('company_name')} (CIK: {h.get('cik')})\n"
            f"Entities: {json.dumps([e.get('name', 'Unknown') for e in h.get('raw_entities', [])])}"
            for h in historical_entities[:10]  # Limit to 10 most recent filings
        ])
        
        # Create a prompt for finding links
        prompt_template = f"""
        Current filing information:
        Filing ID: {current_entities.get('filing_id')}
        Date: {current_entities.get('filing_date')}
        Type: {current_entities.get('filing_type')}
        Company: {current_entities.get('company_name')} (CIK: {current_entities.get('cik')})
        
        Current filing entities:
        {json.dumps(current_entities.get('raw_entities', []), indent=2)}
        
        Historical filing information:
        {historical_context}
        
        Task: Identify meaningful connections between entities in the current filing and historical filings.
        For each connection, specify:
        1. The entities involved
        2. The nature of the relationship
        3. Any notable changes or developments
        4. Potential significance of the connection
        
        Format your response as a list of connections with detailed explanations.
        """
        
        # Call the model for entity linking
        result = await self.model_client.analyze_text(
            text=prompt_template,
            task_type="analysis"
        )
        
        # Parse the model response to extract relationship information
        # In a real system, we would use more robust parsing
        link_text = result.get("analysis", "")
        
        # Extract links from the model output
        links = self._parse_links(link_text)
        
        return {
            "filing_id": current_entities.get("filing_id", "unknown"),
            "links": links,
            "link_text": link_text,
            "new_entities": current_entities.get("raw_entities", []),
            "link_timestamp": datetime.now().isoformat()
        }
    
    def _parse_links(self, link_text: str) -> List[Dict[str, Any]]:
        """
        Parse entity links from model output.
        
        Args:
            link_text: The text output from the model
            
        Returns:
            List of link dictionaries
        """
        links = []
        
        # This is a simplified parser - in production, we would use
        # a more robust approach with better structure detection
        
        # Split by numbered items or sections
        link_blocks = re.split(r'\n\s*(?:\d+\.|\*|\-)\s*', link_text)
        
        for block in link_blocks:
            block = block.strip()
            if not block or len(block) < 20:  # Skip empty or very short blocks
                continue
                
            link = {
                "description": block,
                "entities_involved": [],
                "relationship_type": "related",
                "confidence": "medium"
            }
            
            # Try to extract entity names
            entity_names = re.findall(r'(?:entity|company|person|organization):\s*([^,\n]+)', block, re.IGNORECASE)
            if entity_names:
                link["entities_involved"] = [name.strip() for name in entity_names]
            
            # Try to extract relationship type
            rel_match = re.search(r'(?:relationship|connection|link):\s*([^,\n]+)', block, re.IGNORECASE)
            if rel_match:
                link["relationship_type"] = rel_match.group(1).strip()
            
            # Look for significance indicators
            if re.search(r'significant|important|critical|major', block, re.IGNORECASE):
                link["significance"] = "high"
            elif re.search(r'minor|small|slight', block, re.IGNORECASE):
                link["significance"] = "low"
            else:
                link["significance"] = "medium"
                
            links.append(link)
        
        return links

async def test_entity_linker():
    """Test the entity linker functionality."""
    linker = EntityLinker()
    
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
    
    Prior to joining Columbia Law School, Ms. Andrias served as Special Assistant to the President and 
    Senior Counsel in the White House Counsel's Office from January 2021 to August 2021.
    """
    
    sample_metadata = {
        "accession_number": "0000320193-23-000022",
        "company_name": "APPLE INC",
        "cik": "0000320193",
        "form_type": "8-K",
        "filing_date": "2023-03-01"
    }
    
    # Extract entities
    entities_result = await linker.extract_entities(sample_filing, sample_metadata)
    
    print(f"Extracted entities: {json.dumps(entities_result.get('raw_entities', []), indent=2)}")
    
    # Simulate historical entities
    historical_entities = [{
        "filing_id": "0000320193-23-000010",
        "filing_date": "2023-01-15",
        "filing_type": "8-K",
        "company_name": "APPLE INC",
        "cik": "0000320193",
        "raw_entities": [
            {
                "name": "Katherine Adams",
                "type": "person",
                "role": "Senior Vice President, General Counsel",
                "context": "Katherine Adams mentioned as part of the leadership team"
            },
            {
                "name": "Tim Cook",
                "type": "person",
                "role": "CEO",
                "context": "Tim Cook announced quarterly results"
            }
        ]
    }]
    
    # Link entities
    links_result = await linker.link_entities(entities_result, historical_entities)
    
    print(f"Entity links: {json.dumps(links_result.get('links', []), indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_entity_linker())