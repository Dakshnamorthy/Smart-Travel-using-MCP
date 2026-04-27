import React from 'react';

const MessageBubble = ({ message, onSave }) => {
  const isAI = message.role === 'ai';

  // Extract raw text rendering to support newline splits properly
  const formatText = (text) => {
    return text.split('\n').map((str, idx) => (
      <React.Fragment key={idx}>
        {str}
        <br />
      </React.Fragment>
    ));
  };

  return (
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: isAI ? 'flex-start' : 'flex-end',
      maxWidth: '100%'
    }}>
      <div style={{
        padding: '10px 14px', 
        backgroundColor: isAI ? 'var(--color-bg-bubble-in)' : 'var(--color-bg-bubble-out)',
        borderRadius: '8px',
        borderTopLeftRadius: isAI ? '0' : '8px',
        borderTopRightRadius: isAI ? '8px' : '0',
        color: 'var(--color-text-primary)',
        width: 'fit-content',
        maxWidth: '85%',
        boxShadow: '0 1px 0.5px rgba(0,0,0,0.13)',
        position: 'relative'
      }}>
        {/* Actual Message Text */}
        <div style={{ wordWrap: 'break-word', whiteSpace: 'pre-wrap' }}>
          {formatText(message.text)}
        </div>

        {/* Feature Inject: "Save Trip" Contextual Button rendering conditionally */}
        {isAI && message.isPlanning && (
          <div style={{ marginTop: '12px', borderTop: '1px solid var(--color-divider)', paddingTop: '8px' }}>
            <button 
              onClick={onSave}
              style={{
                backgroundColor: 'var(--color-secondary)',
                color: 'white',
                fontWeight: 'bold',
                padding: '6px 16px',
                borderRadius: '16px',
                fontSize: '13px',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              🏷️ Save This Trip
            </button>
          </div>
        )}
        
        {/* Tiny timestamp styling */}
        <div style={{ 
          fontSize: '11px', 
          color: 'var(--color-text-meta)', 
          textAlign: 'right', 
          marginTop: '4px' 
        }}>
          Now
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;
