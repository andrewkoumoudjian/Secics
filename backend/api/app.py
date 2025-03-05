"""
FastAPI application for SEC filings monitoring and analysis.
Provides API endpoints for accessing filing insights and streaming analysis.
"""
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json
import os

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
import uvicorn
from pydantic import BaseModel

# Import our modules
from backend.data_collection.rss_fetcher import SECRSSFetcher
from backend.data_collection.edgar_client import EDGARClient
from backend.analysis.filing_analyzer import FilingAnalyzer
from backend.analysis.entity_linker import EntityLinker
from backend.analysis.event_detector import EventDetector
from backend.analysis.models import ModelClient
from backend.storage.gcs_client import GCSClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="SEC Insights API",
    description="API for SEC filings monitoring and analysis",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize clients
model_client = ModelClient()
edgar_client = EDGARClient()
analyzer = FilingAnalyzer(model_client=model_client)
entity_linker = EntityLinker(model_client=model_client)
event_detector = EventDetector(model_client=model_client)
gcs_client = GCSClient()

# Store active SSE connections
active_connections = set()

# Pydantic models for request/response validation
class FilingRequest(BaseModel):
    filing_id: str
    content: Optional[str] = None
    metadata: Dict[str, Any]

class AnalysisRequest(BaseModel):
    filing_id: str
    analysis_type: str = "full"  # "full", "summary", "events", "entities"

class CompanyQuery(BaseModel):
    cik: str
    name: Optional[str] = None
    limit: int = 100

# API Routes
@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "status": "online",
        "service": "SEC Insights API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/filings")
async def list_filings(
    days: int = Query(30, description="Number of days to look back"),
    limit: int = Query(100, description="Maximum number of filings to return"),
    form_type: Optional[str] = Query(None, description="Filter by form type (e.g. 10-K, 8-K)")
):
    """List recent filings."""
    # This would query our database or storage for recent filings
    # For now, return a placeholder
    return {
        "status": "success",
        "message": "This endpoint would list recent filings",
        "parameters": {
            "days": days,
            "limit": limit,
            "form_type": form_type
        }
    }

@app.get("/filings/{filing_id}")
async def get_filing(filing_id: str = Path(..., description="Filing accession number")):
    """Get a specific filing by ID."""
    filing = gcs_client.retrieve_filing(filing_id)
    if not filing:
        raise HTTPException(status_code=404, detail=f"Filing {filing_id} not found")
    
    return filing

@app.get("/filings/{filing_id}/analysis")
async def get_filing_analysis(filing_id: str = Path(..., description="Filing accession number")):
    """Get analysis for a specific filing."""
    analysis = gcs_client.retrieve_latest_analysis(filing_id)
    if not analysis:
        raise HTTPException(status_code=404, detail=f"Analysis for filing {filing_id} not found")
    
    return analysis

@app.post("/filings/{filing_id}/analyze")
async def analyze_filing(
    filing_id: str,
    background_tasks: BackgroundTasks,
    request: Optional[AnalysisRequest] = None
):
    """Trigger analysis for a filing."""
    filing = gcs_client.retrieve_filing(filing_id)
    if not filing:
        raise HTTPException(status_code=404, detail=f"Filing {filing_id} not found")
    
    # Start background task for analysis
    background_tasks.add_task(
        process_filing_analysis,
        filing_id,
        filing["content"],
        filing["metadata"],
        request.analysis_type if request else "full"
    )
    
    return {
        "status": "success",
        "message": f"Analysis started for filing {filing_id}",
        "analysis_type": request.analysis_type if request else "full"
    }

@app.get("/companies/{cik}/filings")
async def get_company_filings(
    cik: str = Path(..., description="Company CIK number"),
    limit: int = Query(100, description="Maximum number of filings to return")
):
    """Get filings for a specific company."""
    filings = gcs_client.list_filings_by_company(cik, limit=limit)
    return {
        "cik": cik,
        "filings_count": len(filings),
        "filings": filings
    }

@app.get("/events/critical")
async def get_critical_events(
    days: int = Query(30, description="Number of days to look back"),
    limit: int = Query(100, description="Maximum number of events to return")
):
    """Get critical events detected in recent filings."""
    events = gcs_client.list_critical_events(days_back=days, limit=limit)
    return {
        "events_count": len(events),
        "days_back": days,
        "events": events
    }

@app.get("/stream")
async def stream_events():
    """Stream real-time filing analyses and events."""
    async def event_generator():
        connection_id = id(asyncio)  # Unique ID for this connection
        active_connections.add(connection_id)
        
        try:
            # Send initial message
            yield f"data: {json.dumps({'event': 'connection_established', 'timestamp': datetime.now().isoformat()})}\n\n"
            
            # Keep connection alive and stream events
            while True:
                # In a real implementation, this would pull from a queue of events
                await asyncio.sleep(10)
                
                # Check if client disconnected
                if connection_id not in active_connections:
                    break
                
                # Send heartbeat
                yield f"data: {json.dumps({'event': 'heartbeat', 'timestamp': datetime.now().isoformat()})}\n\n"
        except asyncio.CancelledError:
            # Client disconnected
            active_connections.remove(connection_id)
        finally:
            if connection_id in active_connections:
                active_connections.remove(connection_id)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

# Background tasks
async def process_filing_analysis(filing_id: str, content: str, metadata: Dict[str, Any], analysis_type: str):
    """Process filing analysis in the background."""
    try:
        logger.info(f"Starting analysis for filing {filing_id}")
        
        # Get company info
        company_info = None
        if "cik" in metadata:
            company_info = await edgar_client.get_company_info(metadata["cik"])
        
        # Run full or specific analysis
        if analysis_type in ["full", "summary"]:
            analysis_result = await analyzer.analyze_filing(content, metadata, company_info)
            gcs_client.store_analysis(filing_id, analysis_result)
            broadcast_event({"event": "analysis_complete", "filing_id": filing_id})
        
        if analysis_type in ["full", "events"]:
            events_result = await event_detector.detect_events(content, metadata)
            gcs_client.store_events(filing_id, events_result)
            broadcast_event({"event": "events_detected", "filing_id": filing_id, "critical": events_result.get("has_critical_events", False)})
        
        if analysis_type in ["full", "entities"]:
            entities_result = await entity_linker.extract_entities(content, metadata)
            gcs_client.store_entities(filing_id, entities_result)
            
            # Get historical entities for linking (up to 10 most recent for this company)
            historical_entities = []  # In a real system, fetch from database or storage
            
            links_result = await entity_linker.link_entities(entities_result, historical_entities)
            gcs_client.store_links(filing_id, links_result)
            
            broadcast_event({"event": "entities_linked", "filing_id": filing_id})
        
        logger.info(f"Completed analysis for filing {filing_id}")
        
    except Exception as e:
        logger.error(f"Error processing filing {filing_id}: {str(e)}")
        broadcast_event({"event": "analysis_error", "filing_id": filing_id, "error": str(e)})

def broadcast_event(event_data: Dict[str, Any]):
    """Broadcast an event to all connected clients."""
    # In a real implementation, this would use a message queue or similar
    event_json = json.dumps(event_data)
    event_message = f"data: {event_json}\n\n"
    logger.info(f"Broadcasting event: {event_json}")
    
    # Nothing more to do in this simplified implementation
    # In production, would push to connected clients

# RSS feed monitoring
async def start_rss_monitoring():
    """Start monitoring SEC RSS feeds."""
    rss_fetcher = SECRSSFetcher(poll_interval=300)  # Check every 5 minutes
    await rss_fetcher.monitor_feeds(process_new_filing)

async def process_new_filing(feed_name: str, entries: List[Any]):
    """Process new filings from RSS feeds."""
    logger.info(f"Processing {len(entries)} new filings from {feed_name}")
    
    for entry in entries:
        try:
            # Extract filing ID from entry (simplified)
            filing_id = entry.id.split("/")[-1]
            
            # Download filing from EDGAR
            logger.info(f"Downloading filing {filing_id}")
            
            # In a real implementation, would extract more metadata
            # and properly download the filing
            
            # Store raw filing
            metadata = {
                "accession_number": filing_id,
                "title": entry.title,
                "link": entry.link,
                "updated": entry.updated if hasattr(entry, "updated") else "",
                "form_type": "unknown",  # Would parse from title or content
                "company_name": "unknown",  # Would extract from content
                "cik": "unknown",  # Would extract from content
                "filing_date": datetime.now().strftime("%Y-%m-%d")
            }
            
            # Notify about new filing
            broadcast_event({
                "event": "new_filing",
                "filing_id": filing_id,
                "metadata": metadata
            })
            
        except Exception as e:
            logger.error(f"Error processing filing entry: {str(e)}")

# Application startup and shutdown
@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    # Start RSS monitoring in the background
    asyncio.create_task(start_rss_monitoring())
    logger.info("SEC Insights API has started")

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("SEC Insights API shutting down")

# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=True
    )