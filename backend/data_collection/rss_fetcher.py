"""
RSS Feed Fetcher for SEC Filings.
Monitors and processes SEC RSS feeds.
"""
import asyncio
import feedparser
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import hashlib
import aiohttp
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SECRSSFetcher:
    """Fetches and processes SEC RSS feeds."""
    
    # SEC RSS Feed URLs
    RSS_FEEDS = {
        "latest_filings": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=&company=&dateb=&owner=include&start=0&count=40&output=atom",
        "company_filings": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=&dateb=&owner=exclude&start=0&count=40&output=atom",
        "form_4": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=4&company=&dateb=&owner=only&start=0&count=40&output=atom",
        "form_8k": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=8-K&company=&dateb=&owner=exclude&start=0&count=40&output=atom",
        "form_10k": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=10-K&company=&dateb=&owner=exclude&start=0&count=40&output=atom",
        "form_10q": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=10-Q&company=&dateb=&owner=exclude&start=0&count=40&output=atom",
        "form_s1": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=S-1&company=&dateb=&owner=exclude&start=0&count=40&output=atom",
    }
    
    def __init__(self, poll_interval: int = 300):
        """
        Initialize the RSS fetcher.
        
        Args:
            poll_interval: Time between polling RSS feeds in seconds (default: 5 minutes)
        """
        self.poll_interval = poll_interval
        self.last_seen_entries = {}  # Store hashes of entries we've seen
        self.headers = {
            'User-Agent': 'SEC-Insights-Tool/1.0 (contact@example.com)'
        }
    
    async def fetch_feed(self, feed_url: str) -> Optional[feedparser.FeedParserDict]:
        """Fetch and parse an RSS feed."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(feed_url, headers=self.headers) as response:
                    if response.status != 200:
                        logger.error(f"Error fetching feed {feed_url}: HTTP {response.status}")
                        return None
                    
                    content = await response.text()
                    feed = feedparser.parse(content)
                    return feed
        except Exception as e:
            logger.error(f"Error fetching feed {feed_url}: {str(e)}")
            return None
    
    def _entry_hash(self, entry) -> str:
        """Create a unique hash for an entry to detect duplicates."""
        # Use relevant fields to create a hash
        key_data = f"{entry.id}_{entry.updated if hasattr(entry, 'updated') else ''}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _is_new_entry(self, feed_name: str, entry) -> bool:
        """Check if this is a new entry we haven't processed yet."""
        entry_hash = self._entry_hash(entry)
        
        if feed_name not in self.last_seen_entries:
            self.last_seen_entries[feed_name] = set()
            
        if entry_hash in self.last_seen_entries[feed_name]:
            return False
            
        self.last_seen_entries[feed_name].add(entry_hash)
        return True
    
    async def process_feed(self, feed_name: str, feed_url: str, callback):
        """Process a specific RSS feed and call the callback for new entries."""
        feed = await self.fetch_feed(feed_url)
        if not feed:
            return
            
        new_entries = []
        for entry in feed.entries:
            if self._is_new_entry(feed_name, entry):
                new_entries.append(entry)
                
        if new_entries:
            logger.info(f"Found {len(new_entries)} new entries in {feed_name}")
            await callback(feed_name, new_entries)
    
    async def monitor_feeds(self, callback):
        """
        Continuously monitor all RSS feeds.
        
        Args:
            callback: Async function to call with (feed_name, new_entries) for processing
        """
        while True:
            tasks = []
            for feed_name, feed_url in self.RSS_FEEDS.items():
                # Don't process company-specific feeds here
                if "{cik}" not in feed_url:
                    tasks.append(self.process_feed(feed_name, feed_url, callback))
            
            if tasks:
                await asyncio.gather(*tasks)
            
            logger.info(f"Sleeping for {self.poll_interval} seconds before next poll")
            await asyncio.sleep(self.poll_interval)
    
    async def monitor_company(self, cik: str, callback):
        """
        Monitor filings for a specific company by CIK.
        
        Args:
            cik: Company CIK number
            callback: Async function to call with (feed_name, new_entries) for processing
        """
        feed_url = self.RSS_FEEDS["company_filings"].format(cik=cik)
        feed_name = f"company_{cik}"
        
        while True:
            await self.process_feed(feed_name, feed_url, callback)
            await asyncio.sleep(self.poll_interval)

async def example_callback(feed_name, entries):
    """Example callback function to process new entries."""
    for entry in entries:
        logger.info(f"New filing in {feed_name}: {entry.title}")
        # Here you would add code to send the entry for further processing

async def main():
    """Main function to demonstrate the RSS fetcher."""
    fetcher = SECRSSFetcher(poll_interval=60)  # Poll every minute for demo
    await fetcher.monitor_feeds(example_callback)

if __name__ == "__main__":
    asyncio.run(main())