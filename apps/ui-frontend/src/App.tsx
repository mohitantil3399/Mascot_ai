// apps/ui-frontend/src/App.tsx
import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useNativeBridge } from './hooks/useNativeBridge';
import { useAIStream } from './hooks/useAIStream';
import PetCanvas from './components/pet/PetCanvas';
import ChatBubble from './components/chat/ChatBubble';
import InputBar from './components/chat/InputBar';
import type { NativeMessage } from './types/ipc';

type PetState = 'idle' | 'thinking' | 'talking';

// ⚠️ CRITICAL: Ensure these match the exact dimensions in your index.css
const PET_W = 160;
const PET_H = 160;
const CHAT_W = 360;
const CHAT_H = 480;

export default function App() {
  const [petState, setPetState] = useState<PetState>('idle');
  const [connectionStatus, setConnectionStatus] = useState<string>('connecting');
  const [isChatOpen, setIsChatOpen] = useState<boolean>(false);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [petPos] = useState({
    x: 15,
    y: 36,
  });

  const dragRef = useRef<{
    isPointerDown: boolean;
    hasMoved: boolean;
    lastScreenX: number;
    lastScreenY: number;
    startScreenX: number;
    startScreenY: number;
    lastDragEndTime: number;
  }>({
    isPointerDown: false,
    hasMoved: false,
    lastScreenX: 0,
    lastScreenY: 0,
    startScreenX: 0,
    startScreenY: 0,
    lastDragEndTime: 0,
  });

  const { response, isStreaming, startStream, appendChunk, endStream, resetStream } = useAIStream();

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
      case 'session_reset':
        resetStream();
        setPetState('idle');
        break;
      case 'error':
        appendChunk(`\n\n[Error] ${msg.payload}`);
        endStream();
        setPetState('idle');
        break;
    }
  }, [isStreaming, startStream, appendChunk, endStream, resetStream]);

  const { postToNative, isNative } = useNativeBridge(handleNativeMessage);

  const updateRegions = useCallback((_dragging: boolean = false, overrideChatOpen?: boolean) => {
    const chatIsOpen = overrideChatOpen !== undefined ? overrideChatOpen : isChatOpen;
    postToNative({
      type: 'set_chat_open',
      isOpen: chatIsOpen,
    });
    postToNative({
      type: 'update_regions',
      regions: { chatRect: chatIsOpen ? [0, 0, 100, 100] : null },
    });
  }, [isChatOpen, postToNative]);

  useEffect(() => {
    updateRegions(false);
    const handleResize = () => updateRegions(false);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [updateRegions, isChatOpen, petPos]);

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

  const handlePetPointerDown = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    try {
      e.currentTarget.setPointerCapture(e.pointerId);
    } catch {}
    dragRef.current = {
      isPointerDown: true,
      hasMoved: false,
      lastScreenX: e.screenX,
      lastScreenY: e.screenY,
      startScreenX: e.screenX,
      startScreenY: e.screenY,
      lastDragEndTime: dragRef.current.lastDragEndTime,
    };
  }, []);

  const handlePetPointerMove = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    if (!dragRef.current.isPointerDown) return;
    const dx = e.screenX - dragRef.current.lastScreenX;
    const dy = e.screenY - dragRef.current.lastScreenY;
    if (dx === 0 && dy === 0) return;

    if (Math.hypot(e.screenX - dragRef.current.startScreenX, e.screenY - dragRef.current.startScreenY) > 5) {
      if (!dragRef.current.hasMoved) {
        dragRef.current.hasMoved = true;
        setIsDragging(true);
      }
    }

    dragRef.current.lastScreenX = e.screenX;
    dragRef.current.lastScreenY = e.screenY;

    postToNative({ type: 'move_window', dx, dy });
  }, [postToNative]);

  const handlePetPointerUp = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    if (dragRef.current.isPointerDown) {
      if (dragRef.current.hasMoved) {
        dragRef.current.lastDragEndTime = Date.now();
      }
      dragRef.current.isPointerDown = false;
      setIsDragging(false);
      try {
        e.currentTarget.releasePointerCapture(e.pointerId);
      } catch {}
    }
  }, []);

  const handlePetDoubleClick = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    // Ignore double-click if the pet was dragged across the screen (>5px or within 300ms of drag end)
    if (dragRef.current.hasMoved || (Date.now() - dragRef.current.lastDragEndTime < 300)) {
      dragRef.current.hasMoved = false; // Reset for next time
      return;
    }
    const newState = !isChatOpen;
    setIsChatOpen(newState);
    if (newState) {
      resetStream();
      postToNative({ type: 'start_session' });
    } else {
      postToNative({ type: 'close_session' });
    }
    updateRegions(false, newState);
  }, [isChatOpen, postToNative, updateRegions, resetStream]);

  const handleCloseChat = useCallback(() => {
    setIsChatOpen(false);
    resetStream();
    postToNative({ type: 'close_session' });
    updateRegions(false, false);
  }, [postToNative, updateRegions, resetStream]);

  const handleStreamEnd = useCallback(() => {
    setPetState('idle');
  }, []);

  const chatX = 180;
  const chatY = 20;

  return (
    <div className="overlay-root">
      {/* Top-Left Connection Status Pill */}
      <div 
        className={`status-pill status-${connectionStatus}`}
        title={`Status: ${connectionStatus} (Click to reconnect)`}
        onClick={() => !isNative && window.location.reload()}
      >
        <div className="status-dot" />
        {connectionStatus}
        {!isNative && ' (dev mode)'}
      </div>

      {/* 3D Companion Character (Double-click to open session & chat box, click+drag to move anywhere) */}
      <div 
        className="pet-container" 
        style={{ 
          left: `${petPos.x}px`, 
          top: `${petPos.y}px`
        }}
        onPointerDown={handlePetPointerDown}
        onPointerMove={handlePetPointerMove}
        onPointerUp={handlePetPointerUp}
        onDoubleClick={handlePetDoubleClick}
        title="Double-click to open chat box & start session. Click and drag to move character across screen."
      >
        <div 
          className="pet-click-overlay"
          onDoubleClick={handlePetDoubleClick}
          title="Double-click to open chat box & start session. Click and drag to move character across screen."
        />
        <PetCanvas animState={petState} />
      </div>

      {/* Glassmorphic Action Menu & Chat Panel */}
      {isChatOpen && (
        <div 
          className="chat-panel"
          style={{
            left: `${chatX}px`,
            top: `${chatY}px`,
            bottom: 'auto',
            right: 'auto'
          }}
        >
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
              onClick={handleCloseChat}
              title="Close Menu & End Session"
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
