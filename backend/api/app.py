import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("sec-insights")

# Start with logging to debug deployment issues
logger.info(f"Starting SEC Insights API on port {os.environ.get('PORT', 8080)}")

# Create FastAPI app
app = FastAPI(
    title="SEC Insights API",
    description="API for SEC filings monitoring and analysis",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define data models
class FilingEvent(BaseModel):
    category: str
    description: str
    significance: int = 1

class Filing(BaseModel):
    filing_id: str
    company_name: str
    filing_type: str
    filing_date: str
    url: str
    summary: Optional[str] = None
    events: Optional[List[FilingEvent]] = None

# Dummy data for testing
SAMPLE_FILINGS = [
    Filing(
        filing_id="0001193125-21-123456",
        company_name="Example Corp",
        filing_type="10-K",
        filing_date="2021-04-15",
        url="https://www.sec.gov/example",
        summary="Annual report for fiscal year ending December 31, 2020",
        events=[
            FilingEvent(
                category="Management Change",
                description="CFO resignation announced effective June 1, 2021",
                significance=3
            )
        ]
    )
]

@app.get("/")
def root():
    """Health check endpoint"""
    logger.info("Health check endpoint called")
    return {"status": "online", "service": "SEC Insights API"}

@app.get("/filings", response_model=Dict[str, Any])
def get_filings(
    days: int = 30,
    form_type: Optional[str] = None
):
    """Get recent SEC filings with optional filters"""
    logger.info(f"Getting filings for last {days} days, form type: {form_type}")
    
    # Apply filters (this would connect to a real data source in production)
    filtered_filings = SAMPLE_FILINGS
    if form_type:
        filtered_filings = [f for f in filtered_filings if f.filing_type == form_type]
    
    return {
        "filings": filtered_filings,
        "count": len(filtered_filings),
        "days": days
    }

@app.get("/filings/{filing_id}", response_model=Filing)
def get_filing(filing_id: str):
    """Get a specific SEC filing by ID"""
    logger.info(f"Getting filing with ID: {filing_id}")
    
    for filing in SAMPLE_FILINGS:
        if filing.filing_id == filing_id:
            return filing
    
    raise HTTPException(status_code=404, detail="Filing not found")

@app.get("/events/critical", response_model=Dict[str, Any])
def get_critical_events(days: int = 7):
    """Get critical events from recent filings"""
    logger.info(f"Getting critical events for last {days} days")
    
    # In a real app, you would filter for high significance events
    events = []
    for filing in SAMPLE_FILINGS:
        if filing.events:
            for event in filing.events:
                if event.significance >= 3:
                    events.append({
                        "filing_id": filing.filing_id,
                        "company_name": filing.company_name,
                        "filing_type": filing.filing_type,
                        "filing_date": filing.filing_date,
                        "events": [event.dict()]
                    })
    
    return {
        "events": events,
        "count": len(events),
        "days": days
    }

# Admin endpoint for scheduled processing
@app.post("/admin/process_daily")
def process_daily():
    """Process new filings (called by Cloud Scheduler)"""
    logger.info("Running daily processing job")
    # In production, this would fetch and process new filings
    return {"status": "success", "message": "Daily processing completed"}

# Explicitly log when the application starts
logger.info("SEC Insights API initialized successfully")