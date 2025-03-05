import React from "react";
import { motion } from "framer-motion";

export function FilingCard({ filing, expanded, onClick }) {
  // Helper function to get appropriate color based on event criticality
  const getEventColor = (events) => {
    if (!events || events.length === 0) return "#4CAF50"; // Green - No events
    if (events.some(e => e.risk_level === "Critical")) return "#F44336"; // Red - Critical events
    if (events.some(e => e.risk_level === "High")) return "#FF9800"; // Orange - High risk events
    if (events.some(e => e.risk_level === "Medium")) return "#FFEB3B"; // Yellow - Medium risk events
    return "#4CAF50"; // Green - Low risk events
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
      className="filing-card"
      onClick={onClick}
      style={{
        borderRadius: 8,
        padding: 16,
        marginBottom: 16,
        boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
        background: "white",
        cursor: "pointer",
        overflow: "hidden",
        borderLeft: `4px solid ${getEventColor(filing.events)}`
      }}
    >
      <div className="filing-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h3 style={{ margin: 0 }}>{filing.company_name}</h3>
        <div className="filing-meta" style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span className="filing-type" style={{ 
            padding: "2px 8px", 
            borderRadius: 4, 
            background: "#e0e0e0",
            fontSize: 14
          }}>
            {filing.filing_type}
          </span>
          <span className="filing-date" style={{ fontSize: 14, color: "#666" }}>
            {filing.filing_date}
          </span>
        </div>
      </div>

      <motion.div
        initial={false}
        animate={{ height: expanded ? "auto" : 0 }}
        className="filing-content"
        style={{ overflow: "hidden", marginTop: expanded ? 16 : 0 }}
      >
        {filing.summary && (
          <div className="filing-summary" style={{ marginBottom: 16 }}>
            <h4 style={{ margin: "0 0 8px 0", fontSize: 16 }}>Summary</h4>
            <p style={{ margin: 0, fontSize: 14, lineHeight: 1.5 }}>{filing.summary}</p>
          </div>
        )}

        {filing.events && filing.events.length > 0 && (
          <div className="filing-events" style={{ marginBottom: 16 }}>
            <h4 style={{ margin: "0 0 8px 0", fontSize: 16 }}>Significant Events</h4>
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              {filing.events.map((event, index) => (
                <li key={index} style={{ marginBottom: 8, fontSize: 14 }}>
                  <strong>{event.category}</strong>: {event.description}
                  <span style={{ 
                    display: "inline-block",
                    marginLeft: 8,
                    padding: "1px 6px", 
                    borderRadius: 4, 
                    background: event.risk_level === "Critical" ? "#ffcdd2" : 
                               event.risk_level === "High" ? "#ffe0b2" :
                               event.risk_level === "Medium" ? "#fff9c4" : "#e8f5e9",
                    fontSize: 12
                  }}>
                    {event.risk_level}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {filing.entities && filing.entities.length > 0 && (
          <div className="filing-entities" style={{ marginBottom: 16 }}>
            <h4 style={{ margin: "0 0 8px 0", fontSize: 16 }}>Key Entities</h4>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {filing.entities.map((entity, index) => (
                <span key={index} style={{ 
                  padding: "2px 10px", 
                  borderRadius: 16, 
                  background: "#e3f2fd",
                  fontSize: 14
                }}>
                  {entity.name} <small>({entity.type})</small>
                </span>
              ))}
            </div>
          </div>
        )}

        <div className="filing-actions" style={{ display: "flex", justifyContent: "flex-end", gap: 8 }}>
          <button style={{ 
            padding: "6px 12px", 
            border: "none", 
            borderRadius: 4, 
            background: "#2196F3", 
            color: "white",
            cursor: "pointer"
          }}>
            View Full Analysis
          </button>
          <button style={{ 
            padding: "6px 12px", 
            border: "1px solid #2196F3", 
            borderRadius: 4, 
            background: "white", 
            color: "#2196F3",
            cursor: "pointer"
          }}>
            Original Filing
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}