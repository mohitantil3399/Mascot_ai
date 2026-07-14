// apps/ui-frontend/src/types/ipc.d.ts
// Strict typing for the WebView2 bridge — eliminates all @ts-ignore
declare global {
  interface Window {
    chrome?: {
      webview?: {
        postMessage: (message: string) => void;
        addEventListener: (type: string, listener: EventListenerOrEventListenerObject) => void;
        removeEventListener: (type: string, listener: EventListenerOrEventListenerObject) => void;
      };
    };
  }
}

export type NativeMessage =
  | { type: 'ai_chunk'; payload: string }
  | { type: 'status'; payload: 'connecting' | 'connected' | 'reconnecting' | 'error' }
  | { type: 'capture_complete' }
  | { type: 'stream_end' }
  | { type: 'error'; payload: string };

export type ReactToNativeMessage =
  | { type: 'capture_and_ask'; prompt: string }
  | { type: 'toggle_overlay' };
