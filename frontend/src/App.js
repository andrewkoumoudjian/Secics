import React, { useState, useEffect } from 'react';
import './styles/App.css';

function App() {
  const [filings, setFilings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchFilings() {
      try {
        // Replace with your actual API URL when deployed
        const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8080';
        const response = await fetch(`${apiUrl}/filings`);
        
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        
        const data = await response.json();
        setFilings(data.filings || []);
      } catch (err) {
        setError(err.message);
        console.error("Error fetching filings:", err);
      } finally {
        setLoading(false);
      }
    }
    
    fetchFilings();
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <h1>SEC Insights Dashboard</h1>
      </header>
      
      <main>
        {loading && <p>Loading SEC filings...</p>}
        
        {error && <p className="error">Error: {error}</p>}
        
        {!loading && !error && filings.length === 0 && (
          <p>No filings found. Try adjusting your search criteria.</p>
        )}
        
        {filings.length > 0 && (
          <div className="filings-list">
            <h2>Recent Filings</h2>
            {filings.map(filing => (
              <div key={filing.filing_id} className="filing-card">
                <h3>{filing.company_name}</h3>
                <p><strong>Type:</strong> {filing.filing_type}</p>
                <p><strong>Date:</strong> {filing.filing_date}</p>
                {filing.summary && <p>{filing.summary}</p>}
                
                {filing.events && filing.events.length > 0 && (
                  <div className="events">
                    <h4>Key Events:</h4>
                    <ul>
                      {filing.events.map((event, index) => (
                        <li key={index}>
                          <span className="event-category">{event.category}</span>: {event.description}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                
                <a href={filing.url} target="_blank" rel="noopener noreferrer">View Filing</a>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;