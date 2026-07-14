// libs/shared-types/protocol.ts
// Single source of truth for WebSocket & IPC schemas across all 3 tiers

export type WebSocketClientMessage =
  | { type: 'vision_prompt'; prompt: string; roi?: [number, number, number, number] }
  | { type: 'ping' }
  | { type: 'cancel_stream' };

export type WebSocketServerMessage =
  | { type: 'stream_start' }
  | { type: 'token'; payload: string }
  | { type: 'stream_end' }
  | { type: 'stream_cancelled' }
  | { type: 'pong' }
  | { type: 'error'; payload: string };

// WebView2 IPC Messages (React ↔ C# Host)
export type IpcToHostMessage =
  | { type: 'capture_and_ask'; prompt: string }
  | { type: 'set_click_through'; passThrough: boolean }
  | { type: 'minimize_app' }
  | { type: 'close_app' };

export type IpcToUiMessage =
  | { type: 'ai_chunk'; payload: string }
  | { type: 'status'; payload: 'connecting' | 'connected' | 'reconnecting' | 'error' }
  | { type: 'capture_complete' }
  | { type: 'stream_end' }
  | { type: 'error'; payload: string };
