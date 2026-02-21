const { useState, useEffect } = React;

const API_BASE = "http://localhost:8000";

function App() {
  const [userId] = useState("web_user_" + Math.floor(Math.random() * 1000000));
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  
  const [feedbackChosen, setFeedbackChosen] = useState("");
  const [feedbackRating, setFeedbackRating] = useState(5);
  const [feedbackLoading, setFeedbackLoading] = useState(false);
  
  const handleQuery = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, message: query })
      });
      const data = await res.json();
      setResults(data);
      // Reset feedback form
      if (data.top_results && data.top_results.length > 0) {
        setFeedbackChosen(data.top_results[0].item_id);
      }
      setFeedbackRating(5);
    } catch (err) {
      console.error(err);
      alert("Failed to fetch. Make sure FastAPI server is running.");
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = async (e) => {
    e.preventDefault();
    if (!feedbackChosen || !results) return;
    
    setFeedbackLoading(true);
    const notChosenIds = results.top_results
      .filter(r => r.item_id !== feedbackChosen)
      .map(r => r.item_id);
      
    try {
      await fetch(`${API_BASE}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          chosen_item_id: feedbackChosen,
          not_chosen_item_ids: notChosenIds,
          rating: parseInt(feedbackRating)
        })
      });
      alert("Feedback submitted successfully! Re-submitting query to show updated results...");
      // Re-run the same query immediately
      await handleQuery(new Event('submit'));
    } catch (err) {
      console.error(err);
      alert("Failed to submit feedback.");
    } finally {
      setFeedbackLoading(false);
    }
  };

  return (
    <div className="app-container">
      <div className="header">
        <h1>Bite Better</h1>
        <p>Your AI-powered personalized food planner</p>
      </div>

      <form onSubmit={handleQuery} className="search-box">
        <input 
          type="text" 
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. I want a high protein lunch under 20 bucks"
          className="search-input"
          disabled={loading}
        />
        <button type="submit" className="btn" disabled={loading || !query.trim()}>
          {loading ? "Searching..." : "Find"}
        </button>
      </form>

      {loading && <div className="loading">Processing your request...</div>}

      {results && !loading && (
        <div className="results-container">
          {results.coach_text && (
             <div className="coach-section">
               <div className="coach-text">💬 "{results.coach_text}"</div>
               {results.coach_audio_url && (
                 <audio controls autoPlay src={results.coach_audio_url} style={{width: '100%', height: '40px', marginTop: '10px'}}>
                   Your browser does not support the audio element.
                 </audio>
               )}
             </div>
          )}

          <div className="results-grid">
            {results.top_results.map((item, idx) => (
              <div key={item.item_id} className="result-card">
                <div className="result-header">
                  <div>
                    <div className="item-name">#{idx + 1} {item.name}</div>
                    <div className="item-restaurant">from {item.restaurant} • via {item.best_platform.platform}</div>
                  </div>
                  <div className="item-price">
                    ${item.best_platform.effective_price.toFixed(2)}
                  </div>
                </div>
                
                <div className="tags-container">
                  {item.tags.map(t => (
                    <span key={t} className="tag">{t.replace('_', ' ')}</span>
                  ))}
                  <span className="tag" style={{backgroundColor: '#e0f2fe', color: '#0369a1'}}>
                    Score: {item.score.toFixed(2)}
                  </span>
                </div>
                
                <div className="nutrition-container">
                  <div className="nutrition-item">
                    <span className="nutrition-label">Protein</span>
                    <span className="nutrition-value">{item.protein_est}g</span>
                  </div>
                  <div className="nutrition-item">
                     <span className="nutrition-label">Base Price</span>
                     <span className="nutrition-value">${item.best_platform.base_price.toFixed(2)}</span>
                  </div>
                  <div className="nutrition-item">
                     <span className="nutrition-label">Delivery Fee</span>
                     <span className="nutrition-value">${item.best_platform.delivery_fee.toFixed(2)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {results.top_results.length > 0 ? (
            <div className="feedback-section">
              <h3>Help the coach learn your preferences</h3>
              <form onSubmit={handleFeedback} className="feedback-form">
                
                <div className="form-group">
                  <label>Which option did you choose?</label>
                  <select 
                    value={feedbackChosen} 
                    onChange={e => setFeedbackChosen(e.target.value)}
                    className="feedback-select"
                  >
                    {results.top_results.map((item, idx) => (
                      <option key={item.item_id} value={item.item_id}>
                        {idx + 1}. {item.name} ({item.restaurant})
                      </option>
                    ))}
                  </select>
                </div>
                
                <div className="form-group">
                  <label>How satisfied are you with this selection? (1-10)</label>
                  <div className="rating-container">
                    <input 
                      type="range" 
                      min="1" max="10" 
                      value={feedbackRating} 
                      onChange={e => setFeedbackRating(e.target.value)}
                      className="rating-slider"
                    />
                    <span className="rating-value">{feedbackRating}/10</span>
                  </div>
                  <small style={{color: '#64748b'}}>Higher ratings boost these tags & turn up the coach's hype level.</small>
                </div>
                
                <button type="submit" className="btn" disabled={feedbackLoading}>
                  {feedbackLoading ? "Submitting..." : "Submit Feedback & Reroll"}
                </button>
              </form>
            </div>
          ) : (
            <div className="loading">No options matched your constraints.</div>
          )}
        </div>
      )}
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
