// apps/ui-frontend/src/hooks/useNativeBridge.ts
import { useCallback, useEffect, useRef } from 'react';
import type { NativeMessage, ReactToNativeMessage } from '../types/ipc';

type MessageHandler = (msg: NativeMessage) => void;

// When there's no C# WebView2 host (i.e. the app is just opened in a normal
// browser tab for local testing), we still want "Ask" to actually reach the
// Python AI Orchestrator. This talks to the same ws://localhost:8000/ws
// endpoint and follows the same wire protocol the C# host uses:
//   -> text JSON metadata frame  { type: 'vision_prompt', prompt }
//   -> binary JPEG frame
//   <- text JSON frames: stream_start | token | stream_end | error | pong
const BACKEND_WS_URL = 'ws://localhost:8000/ws';

export const useNativeBridge = (onMessage: MessageHandler) => {
  const isNative = !!window.chrome?.webview;
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;

  const wsRef = useRef<WebSocket | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttemptsRef = useRef(0);

  useEffect(() => {
    if (isNative) {
      const handler = (event: Event) => {
        const raw = (event as any).data ?? (event as CustomEvent<NativeMessage>).detail;
        let msg = raw;
        if (typeof raw === 'string') {
          try {
            msg = JSON.parse(raw);
          } catch {
            return;
          }
        }
        if (msg && typeof msg === 'object') {
          onMessageRef.current(msg);
        }
      };
      window.chrome!.webview!.addEventListener('message', handler);
      window.chrome!.webview!.postMessage(JSON.stringify({ type: 'get_status' }));
      const statusInterval = setInterval(() => {
        window.chrome!.webview!.postMessage(JSON.stringify({ type: 'get_status' }));
      }, 1500);
      return () => {
        window.chrome!.webview!.removeEventListener('message', handler);
        clearInterval(statusInterval);
      };
    }

    // Browser (standalone) mode: connect for real instead of mocking.
    let cancelled = false;

    const connect = () => {
      if (cancelled) return;
      onMessageRef.current({ type: 'status', payload: reconnectAttemptsRef.current === 0 ? 'connecting' : 'reconnecting' });

      const ws = new WebSocket(BACKEND_WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        reconnectAttemptsRef.current = 0;
        onMessageRef.current({ type: 'status', payload: 'connected' });
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          switch (data.type) {
            case 'token':
              onMessageRef.current({ type: 'ai_chunk', payload: data.payload ?? '' });
              break;
            case 'stream_end':
            case 'stream_cancelled':
              onMessageRef.current({ type: 'stream_end' });
              break;
            case 'session_reset':
              onMessageRef.current({ type: 'session_reset' });
              break;
            case 'error':
              onMessageRef.current({ type: 'error', payload: data.payload ?? 'Unknown error' });
              break;
            // 'stream_start' / 'pong' need no UI action
          }
        } catch {
          // Non-JSON payload — treat as a raw chunk.
          onMessageRef.current({ type: 'ai_chunk', payload: String(event.data) });
        }
      };

      const scheduleReconnect = () => {
        if (cancelled) return;
        reconnectAttemptsRef.current += 1;
        onMessageRef.current({ type: 'status', payload: 'reconnecting' });
        const delay = Math.min(1000 * 2 ** reconnectAttemptsRef.current, 15000);
        reconnectTimerRef.current = setTimeout(connect, delay);
      };

      ws.onerror = () => {
        onMessageRef.current({ type: 'status', payload: 'error' });
      };

      ws.onclose = () => {
        if (wsRef.current === ws) wsRef.current = null;
        scheduleReconnect();
      };
    };

    connect();

    return () => {
      cancelled = true;
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      wsRef.current?.close();
      wsRef.current = null;
      streamRef.current?.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    };
  }, [isNative]);

  // Captures a single frame from the user's screen (browser Screen Capture
  // API) and returns it as JPEG bytes, mirroring what the C# host's
  // GpuScreenCapture does natively.
  const captureScreenFrame = useCallback(async (): Promise<Blob> => {
    if (!streamRef.current) {
      streamRef.current = await navigator.mediaDevices.getDisplayMedia({ video: true });
    }
    const track = streamRef.current.getVideoTracks()[0];
    // Prefer the modern, efficient path when available.
    const ImageCaptureCtor = (window as any).ImageCapture;
    if (ImageCaptureCtor) {
      const capture = new ImageCaptureCtor(track);
      const bitmap = await capture.grabFrame();
      const canvas = document.createElement('canvas');
      canvas.width = bitmap.width;
      canvas.height = bitmap.height;
      const ctx = canvas.getContext('2d')!;
      ctx.drawImage(bitmap, 0, 0);
      return await new Promise<Blob>((resolve, reject) =>
        canvas.toBlob((b) => (b ? resolve(b) : reject(new Error('toBlob failed'))), 'image/jpeg', 0.85)
      );
    }

    // Fallback: grab a frame via a hidden <video> element.
    const video = document.createElement('video');
    video.srcObject = streamRef.current;
    await video.play();
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d')!;
    ctx.drawImage(video, 0, 0);
    return await new Promise<Blob>((resolve, reject) =>
      canvas.toBlob((b) => (b ? resolve(b) : reject(new Error('toBlob failed'))), 'image/jpeg', 0.85)
    );
  }, []);

  const postToNative = useCallback((msg: ReactToNativeMessage) => {
    if (isNative) {
      window.chrome!.webview!.postMessage(JSON.stringify(msg));
      return;
    }

    if (msg.type === 'start_session' || msg.type === 'close_session' || msg.type === 'reset_session') {
      const ws = wsRef.current;
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: msg.type }));
      }
      return;
    }

    if (msg.type !== 'capture_and_ask') return;

    (async () => {
      try {
        const jpegBlob = await captureScreenFrame();
        onMessageRef.current({ type: 'capture_complete' });

        const ws = wsRef.current;
        if (!ws || ws.readyState !== WebSocket.OPEN) {
          onMessageRef.current({ type: 'error', payload: 'Not connected to AI Orchestrator (ws://localhost:8000/ws).' });
          return;
        }

        ws.send(JSON.stringify({ type: 'vision_prompt', prompt: msg.prompt }));
        ws.send(await jpegBlob.arrayBuffer());
      } catch (err) {
        onMessageRef.current({
          type: 'error',
          payload: err instanceof Error ? err.message : 'Screen capture was cancelled or failed.',
        });
      }
    })();
  }, [isNative, captureScreenFrame]);

  return { postToNative, isNative };
};
