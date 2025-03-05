  // Fetch filings on initial load and when filters change
  useEffect(() => {
    fetchFilings();
  }, [filter.timeframe, filter.formType, filter.eventType]);

  // Apply search filter whenever search term or filings change
  useEffect(() => {
    if (!filings.length) {
      setFilteredFilings([]);
      return;
    }
    
    if (!filter.search.trim()) {
      setFilteredFilings(filings);
      return;
    }
    
    const searchTerm = filter.search.toLowerCase();
    const filtered = filings.filter(filing => 
      filing.company_name.toLowerCase().includes(searchTerm) ||
      filing.filing_id.toLowerCase().includes(searchTerm) ||
      filing.summary?.toLowerCase().includes(searchTerm)
    );
    
    setFilteredFilings(filtered);
  }, [filings, filter.search]);

  const fetchFilings = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Convert timeframe filter to days
      const days = filter.timeframe === "7d" ? 7 : 
                   filter.timeframe === "30d" ? 30 :
                   filter.timeframe === "90d" ? 90 : 365;
      
      // Construct API URL with filters
      let url = `https://api.sec-insights.example.com/filings?days=${days}`;
      if (filter.formType !== "all") {
        url += `&form_type=${filter.formType}`;
      }
      
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Filter by event type if needed
      let processedFilings = data.filings;
      if (filter.eventType !== "all") {
        processedFilings = processedFilings.filter(filing => 
          filing.events?.some(event => event.category === filter.eventType)
        );
      }
      
      setFilings(processedFilings);
      // setFilteredFilings will be handled by the search useEffect
      
    } catch (err) {
      console.error("Error fetching filings:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFilingClick = (filingId) => {
    // Toggle expanded state
    setExpandedFilingId(expandedFilingId === filingId ? null : filingId);
  };

  return (
    <div className="dashboard" style={{ maxWidth: 1200, margin: "0 auto", padding: "20px" }}>
      <header style={{ marginBottom: 32 }}>
        <h1 style={{ margin: "0 0 16px 0" }}>SEC Insights Dashboard</h1>
        <div className="dashboard-controls" style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
          {/* Filter controls */}
          <div className="filter-group" style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <label>Form Type:</label>
            <select 
              value={filter.formType} 
              onChange={(e) => setFilter({...filter, formType: e.target.value})}
              style={{ padding: "8px 12px", borderRadius: 4, border: "1px solid #ddd" }}
            >
              <option value="all">All Forms</option>
              <option value="10-K">10-K</option>
              <option value="10-Q">10-Q</option>
              <option value="8-K">8-K</option>
              <option value="4">Form 4</option>
              <option value="13F">13F</option>
            </select>
          </div>
          
          <div className="filter-group" style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <label>Timeframe:</label>
            <select 
              value={filter.timeframe} 
              onChange={(e) => setFilter({...filter, timeframe: e.target.value})}
              style={{ padding: "8px 12px", borderRadius: 4, border: "1px solid #ddd" }}
            >
              <option value="7d">7 Days</option>
              <option value="30d">30 Days</option>
              <option value="90d">90 Days</option>
              <option value="1y">1 Year</option>
            </select>
          </div>
          
          <div className="filter-group" style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <label>Event Type:</label>
            <select 
              value={filter.eventType} 
              onChange={(e) => setFilter({...filter, eventType: e.target.value})}
              style={{ padding: "8px 12px", borderRadius: 4, border: "1px solid #ddd" }}
            >
              <option value="all">All Events</option>
              <option value="Management Change">Management Change</option>
              <option value="Acquisition/Merger">Acquisition/Merger</option>
              <option value="Financial Results">Financial Results</option>
              <option value="Legal Settlement">Legal Settlement</option>
              <option value="Regulatory Issue">Regulatory Issue</option>
            </select>
          </div>
          
          <div className="search-group" style={{ flexGrow: 1 }}>
            <input
              type="text"
              placeholder="Search filings..."
              value={filter.search}
              onChange={(e) => setFilter({...filter, search: e.target.value})}
              style={{ 
                width: "100%", 
                padding: "8px 12px", 
                borderRadius: 4, 
                border: "1px solid #ddd" 
              }}
            />
          </div>
          
          <button 
            onClick={fetchFilings}
            style={{ 
              padding: "8px 16px", 
              borderRadius: 4, 
              border: "none",
              background: "#2196F3",
              color: "white",
              cursor: "pointer"
            }}
          >
            Refresh
          </button>
        </div>
      </header>
      
      <main>
        {loading && (
          <div className="loading" style={{ textAlign: "center", padding: 32 }}>
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
              style={{ 
                width: 40, 
                height: 40, 
                borderRadius: "50%", 
                border: "3px solid #e0e0e0",
                borderTopColor: "#2196F3",
                margin: "0 auto 16px auto"
              }}
            />
            <p>Loading filings...</p>
          </div>
        )}
        
        {error && (
          <div className="error" style={{ 
            padding: 16, 
            background: "#ffebee", 
            borderRadius: 4, 
            color: "#d32f2f",
            marginBottom: 16 
          }}>
            <p style={{ margin: 0 }}><strong>Error:</strong> {error}</p>
          </div>
        )}
        
        {!loading && !error && filteredFilings.length === 0 && (
          <div className="no-results" style={{ textAlign: "center", padding: 32, color: "#666" }}>
            <h3>No filings found</h3>
            <p>Try adjusting your filter criteria or check back later.</p>
          </div>
        )}
        
        <div className="filings-list">
          <AnimatePresence>
            {filteredFilings.map(filing => (
              <FilingCard 
                key={filing.filing_id} 
                filing={filing} 
                expanded={expandedFilingId === filing.filing_id}
                onClick={() => handleFilingClick(filing.filing_id)}
              />
            ))}
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}