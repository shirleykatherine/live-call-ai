/**
 * useCallSession hook — central state manager for an active call.
 * Manages WebSocket connection, transcript, and AI analysis state.
 */
import { useState, useCallback, useRef, useEffect } from 'react';
import { CallWebSocket } from '../services/websocket';
import type { WSMessage } from '../services/websocket';
import { api } from '../services/api';
import type {
  TranscriptEntry,
  AgentAnalysis,
  CallSummary,
  CallStatus,
  ConnectionStatus,
} from '../types';

export function useCallSession() {
  const [callId, setCallId] = useState<string | null>(null);
  const [callStatus, setCallStatus] = useState<CallStatus>('idle');
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
  const [analysis, setAnalysis] = useState<AgentAnalysis | null>(null);
  const [summary, setSummary] = useState<CallSummary | null>(null);
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [selectedCustomerId, setSelectedCustomerId] = useState<string>('CUST-001');

  const wsRef = useRef<CallWebSocket | null>(null);

  // Handle incoming WebSocket messages
  const handleMessage = useCallback((message: WSMessage) => {
    switch (message.type) {
      case 'transcript': {
        const d = message.data as unknown as TranscriptEntry;
        setTranscript((prev) => {
          // Avoid duplicate entries
          if (prev.some((t) => t.id && t.id === d.id)) return prev;
          return [...prev, d];
        });
        break;
      }
      case 'analysis': {
        setAnalysis(message.data as unknown as AgentAnalysis);
        break;
      }
      case 'status': {
        const d = message.data as { status: string; message?: string };
        setStatusMessage(d.message || '');
        if (d.status === 'connected') {
          setConnectionStatus('connected');
          setCallStatus('active');
        } else if (d.status === 'analyzing') {
          setCallStatus('analyzing');
        } else if (d.status === 'ready') {
          setCallStatus('active');
        } else if (d.status === 'generating_summary') {
          setCallStatus('generating_summary');
        }
        break;
      }
      case 'summary': {
        const d = message.data as { summary: CallSummary };
        setSummary(d.summary);
        setCallStatus('ended');
        break;
      }
      case 'error': {
        const d = message.data as { message: string };
        setStatusMessage(`Error: ${d.message}`);
        break;
      }
    }
  }, []);

  const startCall = useCallback(async (customerId?: string) => {
    try {
      setCallStatus('idle');
      setTranscript([]);
      setAnalysis(null);
      setSummary(null);
      setConnectionStatus('connecting');
      setStatusMessage('Starting call...');

      const call = await api.startCall(customerId);
      setCallId(call.id);

      const ws = new CallWebSocket(call.id);
      wsRef.current = ws;
      ws.onMessage(handleMessage);
      ws.connect();
      setConnectionStatus('connecting');
    } catch (err) {
      console.error('Failed to start call:', err);
      setConnectionStatus('error');
      setStatusMessage('Failed to start call. Is the backend running?');
    }
  }, [handleMessage]);

  const endCall = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.endCall();
    }
    setCallStatus('generating_summary');
  }, []);

  const sendTranscript = useCallback(
    (speaker: 'customer' | 'agent', text: string) => {
      if (!wsRef.current || !callId) return;
      wsRef.current.sendTranscript(speaker, text, selectedCustomerId || undefined);
    },
    [wsRef, callId, selectedCustomerId]
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      wsRef.current?.disconnect();
    };
  }, []);

  return {
    callId,
    callStatus,
    connectionStatus,
    transcript,
    analysis,
    summary,
    statusMessage,
    selectedCustomerId,
    setSelectedCustomerId,
    startCall,
    endCall,
    sendTranscript,
    isCallActive: callStatus === 'active' || callStatus === 'analyzing',
  };
}
