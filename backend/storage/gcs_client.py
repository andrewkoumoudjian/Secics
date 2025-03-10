"""
Google Cloud Storage client for storing and retrieving SEC filing analyses.
Handles storing raw filings, analyses, and managing data lifecycle.
"""
import os
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import asyncio

from google.cloud import storage
from google.cloud.exceptions import NotFound

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GCSClient:
    """Client for interacting with Google Cloud Storage."""
    
    # Default bucket names
    DEFAULT_BUCKETS = {
        "raw_filings": "sec-insights-raw-filings",
        "analyses": "sec-insights-analyses",
        "events": "sec-insights-events",
        "entities": "sec-insights-entities",
        "links": "sec-insights-links",
    }
    
    def __init__(self, 
                 project_id: Optional[str] = None,
                 bucket_prefix: Optional[str] = None,
                 credential_path: Optional[str] = None):
        """
        Initialize the GCS client.
        
        Args:
            project_id: Google Cloud project ID
            bucket_prefix: Optional prefix for bucket names
            credential_path: Path to service account key file
        """
        # Set up credentials if provided
        if credential_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credential_path
        
        self.project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
        if not self.project_id:
            logger.warning("No Google Cloud project ID provided. Using default.")
            self.project_id = "sec-insights-project"
        
        # Initialize storage client
        self.storage_client = storage.Client(project=self.project_id)
        
        # Set up bucket names with optional prefix
        self.buckets = {}
        prefix = f"{bucket_prefix}-" if bucket_prefix else ""
        for key, value in self.DEFAULT_BUCKETS.items():
            self.buckets[key] = f"{prefix}{value}"
        
        # Create buckets if needed
        self._ensure_buckets_exist()
    
    def _ensure_buckets_exist(self):
        """Ensure all required buckets exist."""
        for bucket_type, bucket_name in self.buckets.items():
            try:
                self.storage_client.get_bucket(bucket_name)
                logger.info(f"Bucket {bucket_name} exists.")
            except NotFound:
                logger.info(f"Creating bucket {bucket_name}...")
                try:
                    self.storage_client.create_bucket(bucket_name)
                    logger.info(f"Bucket {bucket_name} created.")
                except Exception as e:
                    logger.error(f"Error creating bucket {bucket_name}: {str(e)}")
    
    def store_raw_filing(self, filing_id: str, content: str, metadata: Dict[str, Any]) -> bool:
        """
        Store a raw SEC filing.
        
        Args:
            filing_id: Filing accession number
            content: Raw filing content
            metadata: Filing metadata
            
        Returns:
            bool: Success status
        """
        try:
            # Get raw filings bucket
            bucket = self.storage_client.get_bucket(self.buckets["raw_filings"])
            
            # Store content
            formatted_id = filing_id.replace("-", "")
            content_blob = bucket.blob(f"{formatted_id}/content.txt")
            content_blob.upload_from_string(content)
            
            # Store metadata
            metadata_blob = bucket.blob(f"{formatted_id}/metadata.json")
            metadata_blob.upload_from_string(json.dumps(metadata, indent=2))
            
            logger.info(f"Successfully stored raw filing {filing_id}")
            return True
        except Exception as e:
            logger.error(f"Error storing raw filing {filing_id}: {str(e)}")
            return False
    
    def store_analysis(self, filing_id: str, analysis_data: Dict[str, Any]) -> bool:
        """
        Store analysis results for a filing.
        
        Args:
            filing_id: Filing accession number
            analysis_data: Analysis results
            
        Returns:
            bool: Success status
        """
        try:
            # Get analyses bucket
            bucket = self.storage_client.get_bucket(self.buckets["analyses"])
            
            # Store analysis
            formatted_id = filing_id.replace("-", "")
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            blob_name = f"{formatted_id}/{timestamp}_analysis.json"
            
            blob = bucket.blob(blob_name)
            blob.upload_from_string(json.dumps(analysis_data, indent=2))
            
            # Also store latest version with fixed name
            latest_blob = bucket.blob(f"{formatted_id}/latest_analysis.json")
            latest_blob.upload_from_string(json.dumps(analysis_data, indent=2))
            
            logger.info(f"Successfully stored analysis for filing {filing_id}")
            return True
        except Exception as e:
            logger.error(f"Error storing analysis for filing {filing_id}: {str(e)}")
            return False
    
    def store_events(self, filing_id: str, events_data: Dict[str, Any]) -> bool:
        """
        Store detected events for a filing.
        
        Args:
            filing_id: Filing accession number
            events_data: Events detection results
            
        Returns:
            bool: Success status
        """
        try:
            # Get events bucket
            bucket = self.storage_client.get_bucket(self.buckets["events"])
            
            # Store events data
            formatted_id = filing_id.replace("-", "")
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            blob_name = f"{formatted_id}/{timestamp}_events.json"
            
            blob = bucket.blob(blob_name)
            blob.upload_from_string(json.dumps(events_data, indent=2))
            
            # Also store latest version with fixed name
            latest_blob = bucket.blob(f"{formatted_id}/latest_events.json")
            latest_blob.upload_from_string(json.dumps(events_data, indent=2))
            
            # If there are critical events, store a copy in a special directory
            if events_data.get("has_critical_events", False):
                critical_blob = bucket.blob(f"critical/{formatted_id}_{timestamp}.json")
                critical_blob.upload_from_string(json.dumps(events_data, indent=2))
            
            logger.info(f"Successfully stored events for filing {filing_id}")
            return True
        except Exception as e:
            logger.error(f"Error storing events for filing {filing_id}: {str(e)}")
            return False
    
    def store_entities(self, filing_id: str, entities_data: Dict[str, Any]) -> bool:
        """
        Store extracted entities for a filing.
        
        Args:
            filing_id: Filing accession number
            entities_data: Entity extraction results
            
        Returns:
            bool: Success status
        """
        try:
            # Get entities bucket
            bucket = self.storage_client.get_bucket(self.buckets["entities"])
            
            # Store entities data
            formatted_id = filing_id.replace("-", "")
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            blob_name = f"{formatted_id}/{timestamp}_entities.json"
            
            blob = bucket.blob(blob_name)
            blob.upload_from_string(json.dumps(entities_data, indent=2))
            
            # Also store latest version with fixed name
            latest_blob = bucket.blob(f"{formatted_id}/latest_entities.json")
            latest_blob.upload_from_string(json.dumps(entities_data, indent=2))
            
            logger.info(f"Successfully stored entities for filing {filing_id}")
            return True
        except Exception as e:
            logger.error(f"Error storing entities for filing {filing_id}: {str(e)}")
            return False
    
    def store_links(self, filing_id: str, links_data: Dict[str, Any]) -> bool:
        """
        Store entity links for a filing.
        
        Args:
            filing_id: Filing accession number
            links_data: Entity linking results
            
        Returns:
            bool: Success status
        """
        try:
            # Get links bucket
            bucket = self.storage_client.get_bucket(self.buckets["links"])
            
            # Store links data
            formatted_id = filing_id.replace("-", "")
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            blob_name = f"{formatted_id}/{timestamp}_links.json"
            
            blob = bucket.blob(blob_name)
            blob.upload_from_string(json.dumps(links_data, indent=2))
            
            # Also store latest version with fixed name
            latest_blob = bucket.blob(f"{formatted_id}/latest_links.json")
            latest_blob.upload_from_string(json.dumps(links_data, indent=2))
            
            logger.info(f"Successfully stored links for filing {filing_id}")
            return True
        except Exception as e:
            logger.error(f"Error storing links for filing {filing_id}: {str(e)}")
            return False
    
    def retrieve_filing(self, filing_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a raw filing and its metadata.
        
        Args:
            filing_id: Filing accession number
            
        Returns:
            Dict containing filing content and metadata, or None if not found
        """
        try:
            # Get raw filings bucket
            bucket = self.storage_client.get_bucket(self.buckets["raw_filings"])
            
            # Retrieve content and metadata
            formatted_id = filing_id.replace("-", "")
            content_blob = bucket.blob(f"{formatted_id}/content.txt")
            metadata_blob = bucket.blob(f"{formatted_id}/metadata.json")
            
            content = content_blob.download_as_text()
            metadata = json.loads(metadata_blob.download_as_text())
            
            return {
                "filing_id": filing_id,
                "content": content,
                "metadata": metadata
            }
        except NotFound:
            logger.warning(f"Filing {filing_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error retrieving filing {filing_id}: {str(e)}")
            return None
    
    def retrieve_latest_analysis(self, filing_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the latest analysis for a filing.
        
        Args:
            filing_id: Filing accession number
            
        Returns:
            Dict containing analysis data, or None if not found
        """
        try:
            # Get analyses bucket
            bucket = self.storage_client.get_bucket(self.buckets["analyses"])
            
            # Retrieve latest analysis
            formatted_id = filing_id.replace("-", "")
            blob = bucket.blob(f"{formatted_id}/latest_analysis.json")
            
            analysis_data = json.loads(blob.download_as_text())
            return analysis_data
        except NotFound:
            logger.warning(f"No analysis found for filing {filing_id}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving analysis for filing {filing_id}: {str(e)}")
            return None
    
    def list_filings_by_company(self, cik: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List all filings stored for a specific company.
        
        Args:
            cik: Company CIK number
            limit: Maximum number of filings to return
            
        Returns:
            List of filing metadata objects
        """
        try:
            # Get raw filings bucket
            bucket = self.storage_client.get_bucket(self.buckets["raw_filings"])
            
            # List all filing directories that match the CIK
            blobs = bucket.list_blobs()
            filing_ids = set()
            
            for blob in blobs:
                if "/metadata.json" in blob.name:
                    # Get the metadata to check the CIK
                    metadata = json.loads(blob.download_as_text())
                    if metadata.get("cik") == cik:
                        filing_id = metadata.get("accession_number")
                        if filing_id:
                            filing_ids.add(filing_id)
                            
                    if len(filing_ids) >= limit:
                        break
            
            # Retrieve metadata for each filing ID
            filings = []
            for filing_id in filing_ids:
                formatted_id = filing_id.replace("-", "")
                metadata_blob = bucket.blob(f"{formatted_id}/metadata.json")
                metadata = json.loads(metadata_blob.download_as_text())
                filings.append(metadata)
            
            return filings
        except Exception as e:
            logger.error(f"Error listing filings for company {cik}: {str(e)}")
            return []
    
    def list_critical_events(self, days_back: int = 30, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List all critical events detected within a time period.
        
        Args:
            days_back: Number of days to look back
            limit: Maximum number of events to return
            
        Returns:
            List of critical event objects
        """
        try:
            # Get events bucket
            bucket = self.storage_client.get_bucket(self.buckets["events"])
            
            # List all critical event files
            blobs = bucket.list_blobs(prefix="critical/")
            critical_events = []
            
            for blob in blobs:
                try:
                    # Check if the blob is recent enough
                    event_data = json.loads(blob.download_as_text())
                    event_date_str = event_data.get("filing_date")
                    if event_date_str:
                        event_date = datetime.strptime(event_date_str, "%Y-%m-%d")
                        cutoff_date = datetime.now() - timedelta(days=days_back)
                        
                        if event_date >= cutoff_date:
                            critical_events.append(event_data)
                            
                    if len(critical_events) >= limit:
                        break
                except Exception as e:
                    logger.error(f"Error processing event blob {blob.name}: {str(e)}")
                    continue
            
            return critical_events
        except Exception as e:
            logger.error(f"Error listing critical events: {str(e)}")
            return []

def test_gcs_client():
    """Test GCS client functionality."""
    import os
    
    # This is a simple test function that would be expanded in a real implementation
    # In practice, you would use actual GCP credentials
    
    # Check for GCP credentials
    if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
        print("No GCP credentials found. Running in demo mode.")
        print("In production, set GOOGLE_APPLICATION_CREDENTIALS to your service account key path.")
    
    # Create client with test bucket prefix
    client = GCSClient(bucket_prefix="test")
    
    # Example filing metadata
    sample_metadata = {
        "accession_number": "0000320193-23-000022",
        "company_name": "APPLE INC",
        "cik": "0000320193",
        "form_type": "8-K",
        "filing_date": "2023-03-01"
    }
    
    # Store a sample filing
    print("Storing sample filing...")
    client.store_raw_filing(
        filing_id=sample_metadata["accession_number"],
        content="This is a sample filing content.",
        metadata=sample_metadata
    )
    
    # Store sample analysis
    print("Storing sample analysis...")
    sample_analysis = {
        "filing_id": sample_metadata["accession_number"],
        "summary": "This is a sample filing analysis.",
        "analysis_timestamp": datetime.now().isoformat()
    }
    client.store_analysis(
        filing_id=sample_metadata["accession_number"],
        analysis_data=sample_analysis
    )
    
    # Retrieve the stored analysis
    print("Retrieving sample analysis...")
    retrieved_analysis = client.retrieve_latest_analysis(sample_metadata["accession_number"])
    if retrieved_analysis:
        print(f"Successfully retrieved analysis: {json.dumps(retrieved_analysis, indent=2)}")
    else:
        print("Failed to retrieve analysis.")

if __name__ == "__main__":
    test_gcs_client()
