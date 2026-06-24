import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Welcome to the Boston International College Assistant! Ask me anything about our BBA, MBA, BHM programs, admissions, or campus details in Chitwan.' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const res = await axios.post("http://127.0.0.1:8000/chat", {
        session_id: "bic_session",
        message: input
      });
      setMessages(prev => [...prev, { role: 'assistant', content: res.data.response, source: res.data.source_used }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: "⚠️ Connection Error: Unable to reach the campus server cluster." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      {/* Structural Sidebar */}
      <div className="sidebar">
        <div>
          <h2 className="sidebar-title">BIC Assistant</h2>
          <div className="upload-card">
            <p style={{ fontSize: '0.85rem', color: '#9ca3af', lineHeight: '1.4' }}>
              Connected to Boston International College knowledge index. Web nodes are crawled and indexed directly through backend operations.
            </p>
          </div>
        </div>
        <div className="sidebar-footer">Database Status: Sync Complete</div>
      </div>

      {/* Main Chat Feed Panel */}
      <div className="chat-panel">
        <div className="chat-messages">
          {messages.map((msg, i) => (
            <div key={i} className={`message-row ${msg.role}`}>
              <div className="bubble">
                <p>{msg.content}</p>
                {msg.source && msg.source !== "None" && (
                  <span className="source-tag">Reference Node: {msg.source}</span>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="message-row assistant">
              <div className="bubble thinking-bubble">Searching campus index...</div>
            </div>
          )}
        </div>

        {/* User Input Actions */}
        <form onSubmit={handleSend} className="input-form">
          <input 
            type="text" 
            value={input} 
            onChange={(e) => setInput(e.target.value)} 
            placeholder="Ask about admissions, academic programs..." 
            className="chat-input" 
          />
          <button type="submit" className="btn-send">Send</button>
        </form>
      </div>
    </div>
  );
}

export default App;