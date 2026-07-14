// apps/ui-frontend/src/App.tsx
import React, { useState, useCallback } from 'react';
import { useNativeBridge } from './hooks/useNativeBridge';
import { useAIStream } from './hooks/useAIStream';
import PetCanvas from './components/pet/PetCanvas';
import ChatBubble from './components/chat/ChatBubble';
import InputBar from './components/chat/InputBar';
import type { NativeMessage } from './types/ipc';

type PetState = 'idle' | 'thinking' | 'talking';

export default function App() {
  const [petState, setPetState] = useState<PetState>('idle');
  const [connectionStatus, setConnectionStatus] = useState<string>('connecting');
  const [isChatOpen, setIsChatOpen] = useState<boolean>(false);
  const { response, isStreaming, startStream, appendChunk, endStream } = useAIStream();

  const handleNativeMessage = useCallback((msg: NativeMessage) => {
    switch (msg.type) {
      case 'ai_chunk':
        if (!isStreaming) { 
          startStream(); 
          setPetState('talking'); 
          setIsChatOpen(true);
        }
        appendChunk(msg.payload);
        break;
      case 'status':
        setConnectionStatus(msg.payload);
        if (msg.payload === 'connected') setPetState('idle');
        break;
      case 'capture_complete':
        setPetState('thinking');
        break;
      case 'stream_end':
        endStream();
        setPetState('idle');
        break;
      case 'error':
        appendChunk(`\n\n[Error] ${msg.payload}`);
        endStream();
        setPetState('idle');
        break;
    }
  }, [isStreaming, startStream, appendChunk, endStream]);

  const { postToNative, isNative } = useNativeBridge(handleNativeMessage);

  const handleSend = useCallback((prompt: string) => {
    if (!prompt.trim()) return;
    startStream();
    setPetState('thinking');
    setIsChatOpen(true);
    postToNative({ type: 'capture_and_ask', prompt });
  }, [startStream, postToNative]);

  const handleStreamEnd = useCallback(() => {
    endStream();
    setPetState('idle');
  }, [endStream]);

  return (
    <div className="overlay-root">
      {/* Connection status pill */}
      <div className={`status-pill status-${connectionStatus}`}>
        <span className="status-dot" />
        {connectionStatus}
        {!isNative && ' (dev mode)'}
      </div>

      {/* 3D Companion Soldier Character (Click to toggle Chat Box) */}
      <div 
        className="pet-container" 
        onClick={() => setIsChatOpen(prev => !prev)}
        title="Click your companion to toggle chat"
      >
        <PetCanvas animState={petState} />
      </div>

      {/* Glassmorphic Chat Panel (Appears when pet is clicked or active) */}
      {isChatOpen && (
        <div className="chat-panel">
          <ChatBubble
            response={response}
            isStreaming={isStreaming}
            onStreamEnd={handleStreamEnd}
          />
          <InputBar
            onSend={handleSend}
            disabled={isStreaming || connectionStatus === 'reconnecting'}
          />
        </div>
      )}
    </div>
  );
}
