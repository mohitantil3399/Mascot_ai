// apps/ui-frontend/src/App.tsx
import React, { useState, useCallback, useRef } from 'react';
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
  const [isChatOpen, setIsChatOpen] = useState<boolean>(true);
  const lastClickRef = useRef(0);
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

  const handleManualCapture = useCallback(() => {
    startStream();
    setPetState('thinking');
    setIsChatOpen(true);
    postToNative({ 
      type: 'capture_and_ask', 
      prompt: 'Please analyze the current screen capture and highlight any notable UI bugs, code details, or layout elements.' 
    });
  }, [startStream, postToNative]);

  const handlePetClick = useCallback(() => {
    const now = Date.now();
    if (now - lastClickRef.current < 350) {
      // Prevent double-click from immediately reverting the state opened/closed by the first click
      return;
    }
    lastClickRef.current = now;
    setIsChatOpen(prev => !prev);
  }, []);

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

      {/* 3D Companion Character (Single/Double Click to toggle/open menu and chat) */}
      <div 
        className="pet-container" 
        onClick={handlePetClick}
        title="Click or double-click to open screenshot menu & chat box"
      >
        <div 
          className="pet-click-overlay"
          onClick={handlePetClick}
          title="Click or double-click to open screenshot menu & chat box"
        />
        <PetCanvas animState={petState} />
      </div>

      {/* Glassmorphic Action Menu & Chat Panel */}
      {isChatOpen && (
        <div className="chat-panel">
          {/* Header Action Menu */}
          <div className="chat-header">
            <button 
              className="share-screenshot-btn"
              onClick={handleManualCapture}
              disabled={isStreaming || connectionStatus === 'reconnecting'}
              title="Manually capture current screen and send to AI"
            >
              <span>📸</span> Share Screenshot & Analyze
            </button>
            <button 
              className="close-panel-btn"
              onClick={() => setIsChatOpen(false)}
              title="Close Menu"
            >
              ×
            </button>
          </div>

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
