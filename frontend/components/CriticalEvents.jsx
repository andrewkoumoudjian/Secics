import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";

export function CriticalEvents() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    fetchCriticalEvents();
    
    // Set up polling interval
    const interval = setInterval(fetchCriticalEvents, 60000); // Poll every minute
    
    return () => clearInterval(interval);
  }, []);
  
  const fetchCriticalEvents = async () => {
    setLoading(true);
    
    try {
      const response = await fetch("https://api.sec-insights.example.com/events/critical?days=7");
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      const data = await response.json();
      setEvents(data.events || []);
    } catch (err) {
      console.error("Error fetching critical events:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading && events.length === 0) {
    return (
      <div className="critical-events-loading" style={{ padding: 16 }}>
        <p>Loading critical events...</p>
      </div>
    );
  }
  
  if (error && events.length === 0) {
    return (
      <div className="critical-events-error" style={{ padding: 16, color: "#d32f2f" }}>
        <p>Error loading critical events: {error}</p>
      </div>
    );
  }
  
  if (events.length === 0) {
    return (
      <div className="critical-events-empty" style={{ padding: 16 }}>
        <p>No critical events detected in the past 7 days.</p>
      </div>
    );
  }

  return (
    <div className="critical-events" style={{ 
      background: "#fff", 
      borderRadius: 8, 
      boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
      overflow: "hidden"
    }}>
      <div className="critical-events-header" style={{ 
        background: "#d32f2f", 
        color: "white", 
        padding: "12px 16px"
      }}>
        <h3 style={{ margin: 0 }}>Critical Events ({events.length})</h3>
      </div>
      
      <div className="critical-events-list" style={{ maxHeight: 400, overflow: "auto" }}>
        {events.map((event, index) => (
          <motion.div 
            key={`${event.filing_id}-${index}`}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3, delay: index * 0.1 }}
            className="critical-event-item"
            style={{ 
              padding: 16,
              borderBottom: "1px solid #eee"
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
              <strong>{event.company_name}</strong>
              <small>{event.filing_date}</small>
            </div>
            
            <p style={{ margin: "0 0 8px 0" }}>{event.events[0]?.description}</p>
            
            <div style={{ display: "flex", gap: 8 }}>
              <span style={{
                padding: "2px 6px",
                fontSize: 12,
                background: "#ffebee",
                borderRadius: 4,
                color: "#d32f2f"
              }}>
                {event.filing_type}
              </span>
              <span style={{
                padding: "2px 6px",
                fontSize: 12,
                background: "#ffebee",
                borderRadius: 4,
                color: "#d32f2f"
              }}>
                {event.events[0]?.category}
              </span>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}