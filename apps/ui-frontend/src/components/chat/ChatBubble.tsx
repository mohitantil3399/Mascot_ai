// apps/ui-frontend/src/components/chat/ChatBubble.tsx
import React, { useEffect, useRef } from 'react';

interface ChatBubbleProps {
  response: string;
  isStreaming: boolean;
  onStreamEnd: () => void;
}

export default function ChatBubble({ response, isStreaming, onStreamEnd }: ChatBubbleProps) {
  const viewportRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (viewportRef.current) {
      viewportRef.current.scrollTop = viewportRef.current.scrollHeight;
    }
  }, [response]);

  if (!response && !isStreaming) {
    return (
      <div className="chat-bubble-viewport">
        <div className="ai-message" style={{ borderLeftColor: '#8b5cf6' }}>
          👋 <strong>Antigravity Companion Ready!</strong> Ask me about your screen, UI layout bugs, or code snippets.
        </div>
      </div>
    );
  }

  return (
    <div className="chat-bubble-viewport" ref={viewportRef}>
      <div className={`ai-message ${isStreaming ? 'streaming' : ''}`}>
        {response}
      </div>
      {isStreaming && (
        <button 
          onClick={onStreamEnd}
          style={{
            alignSelf: 'flex-end',
            background: 'transparent',
            border: '1px solid rgba(255,255,255,0.2)',
            color: '#cbd5e1',
            borderRadius: '6px',
            padding: '4px 8px',
            fontSize: '0.75rem',
            cursor: 'pointer'
          }}
        >
          ⏹ Stop Streaming
        </button>
      )}
    </div>
  );
}
