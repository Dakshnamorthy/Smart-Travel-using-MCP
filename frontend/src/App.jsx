import React, { useState, useEffect, useRef } from 'react';
import MessageBubble from './components/MessageBubble';
import SavedTrips from './components/SavedTrips';

function App() {
  const [messages, setMessages] = useState([
    { 
      id: '1', 
      role: 'ai', 
      text: 'Hello! 🧭 I am your Smart Travel Planner Agent. Where would you like to plan a trip?',
      isPlanning: false 
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  
  // LocalStorage wrapper state for MVP save_trip functionality
  const [savedTrips, setSavedTrips] = useState(() => {
    const local = localStorage.getItem('saved_trips');
    return local ? JSON.parse(local) : [];
  });
  
  const [showSaved, setShowSaved] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    // Add User Message
    const userMsg = { id: Date.now().toString(), role: 'user', text: inputText };
    setMessages(prev => [...prev, userMsg]);
    setInputText('');
    setIsTyping(true);

    try {
      // POST payload bridging to FastAPI endpoint running on port 8000
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg.text }),
      });

      const data = await response.json();
      
      const aiMsg = { 
        id: (Date.now() + 1).toString(), 
        role: 'ai', 
        text: data.reply,
        isPlanning: data.intent === 'planning'
      };
      
      setMessages(prev => [...prev, aiMsg]);
    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, { 
        id: Date.now().toString(), 
        role: 'ai', 
        text: '❌ Network Error: Make sure the Python FastAPI backend is running on port 8000!' 
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleSaveTrip = (tripText) => {
    const newTrip = {
      id: Date.now().toString(),
      date: new Date().toLocaleDateString(),
      content: tripText
    };
    const updated = [...savedTrips, newTrip];
    setSavedTrips(updated);
    localStorage.setItem('saved_trips', JSON.stringify(updated));
    alert('✅ Trip successfully saved to your vault!');
  };

  const handleDeleteTrip = (id) => {
    const updated = savedTrips.filter(t => t.id !== id);
    setSavedTrips(updated);
    localStorage.setItem('saved_trips', JSON.stringify(updated));
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', position: 'relative' }}>
      
      {/* Sticky Top Header */}
      <header style={{ 
        height: 'var(--header-height)', 
        backgroundColor: 'var(--color-primary)', 
        color: 'white', 
        display: 'flex', 
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 16px', 
        fontSize: '18px', 
        fontWeight: '500',
        zIndex: 10
      }}>
        <div>Smart Travel Agent 🧭</div>
        <button 
          onClick={() => setShowSaved(!showSaved)}
          style={{ 
            color: 'white', 
            fontWeight: 'bold', 
            backgroundColor: 'var(--color-primary-dark)',
            padding: '6px 12px',
            borderRadius: '16px'
          }}>
          {showSaved ? 'Back to Chat' : `Saved Trips (${savedTrips.length})`}
        </button>
      </header>

      {/* Conditional View Layer */}
      {showSaved ? (
        <SavedTrips trips={savedTrips} onDelete={handleDeleteTrip} />
      ) : (
        <>
          {/* Main Scrollable Chat Engine */}
          <main style={{ 
            flex: 1, 
            backgroundColor: 'var(--color-bg-chat)', 
            overflowY: 'auto', 
            padding: '20px 16px',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px'
          }}>
            {messages.map(msg => (
              <MessageBubble 
                key={msg.id} 
                message={msg} 
                onSave={() => handleSaveTrip(msg.text)} 
              />
            ))}
            
            {isTyping && (
             <div style={{ color: 'var(--color-text-meta)', fontStyle: 'italic', fontSize: '13px', alignSelf: 'flex-start' }}>
               Agent is typing...
             </div>
            )}
            
            <div ref={messagesEndRef} />
          </main>

          {/* Sticky Input Footer box */}
          <footer style={{ 
            height: 'var(--footer-height)', 
            backgroundColor: 'var(--color-bg-panel)', 
            padding: '10px 16px', 
            display: 'flex' 
          }}>
            <form onSubmit={handleSend} style={{ display: 'flex', gap: '10px', width: '100%' }}>
              <input 
                type="text" 
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Type your travel query..." 
                style={{ 
                  flex: 1, 
                  padding: '12px 18px', 
                  borderRadius: '24px', 
                  border: 'none',
                  fontSize: '15px'
                }}
              />
            </form>
          </footer>
        </>
      )}
    </div>
  );
}

export default App;
