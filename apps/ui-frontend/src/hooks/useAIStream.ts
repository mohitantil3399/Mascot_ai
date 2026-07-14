// apps/ui-frontend/src/hooks/useAIStream.ts
import { useState, useCallback, useRef } from 'react';

export const useAIStream = () => {
  const [response, setResponse] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const responseRef = useRef('');

  const startStream = useCallback(() => {
    responseRef.current = '';
    setResponse('');
    setIsStreaming(true);
  }, []);

  const appendChunk = useCallback((chunk: string) => {
    responseRef.current += chunk;
    setResponse(responseRef.current);
  }, []);

  const endStream = useCallback(() => {
    setIsStreaming(false);
  }, []);

  return { response, isStreaming, startStream, appendChunk, endStream };
};
