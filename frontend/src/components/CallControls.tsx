/**
 * CallControls — bottom bar with call lifecycle controls.
 */
import { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { CallStatus, ConnectionStatus } from '../types';

interface Props {
  callStatus: CallStatus;
  connectionStatus: ConnectionStatus;
  statusMessage: string;
  selectedCustomerId: string;
  onSetCustomerId: (id: string) => void;
  onStartCall: (customerId?: string) => void;
  onEndCall: () => void;
  callId: string | null;
  isAnalyzing: boolean;
}

export function CallControls({
  callStatus,
  connectionStatus,
  statusMessage,
  selectedCustomerId,
  onSetCustomerId,
  onStartCall,
  onEndCall,
  callId,
  isAnalyzing,
}: Props) {
  const [customers, setCustomers] = useState<{ id: string; name: string }[]>([]);
  const [duration, setDuration] = useState(0);
  const [timerRef, setTimerRef] = useState<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    api.listCustomers()
      .then(setCustomers)
      .catch(() => {});
  }, []);

  // Duration timer
  useEffect(() => {
    if (callStatus === 'active' || callStatus === 'analyzing') {
      const interval = setInterval(() => setDuration((d) => d + 1), 1000);
      setTimerRef(interval);
      return () => clearInterval(interval);
    } else {
      if (timerRef) clearInterval(timerRef);
      if (callStatus === 'idle') setDuration(0);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [callStatus]);

  const formatDuration = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
  };

  const isActive = callStatus === 'active' || callStatus === 'analyzing';

  return (
    <div className="call-controls">
      {/* Left: customer selector */}
      <div className="call-controls-left">
        <select
          className="customer-select"
          value={selectedCustomerId}
          onChange={(e) => onSetCustomerId(e.target.value)}
          disabled={isActive}
          title="Select customer for this call"
        >
          <option value="">— No customer selected —</option>
          {customers.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name} ({c.id})
            </option>
          ))}
        </select>
      </div>

      {/* Center: main controls */}
      <div className="call-controls-center">
        {/* Connection status */}
        <div className="conn-indicator">
          <div className={`conn-dot ${connectionStatus}`} />
          <span className="text-muted">
            {connectionStatus === 'connected' ? 'Connected' :
             connectionStatus === 'connecting' ? 'Connecting...' :
             connectionStatus === 'error' ? 'Connection error' : 'Disconnected'}
          </span>
        </div>

        {/* Duration */}
        {isActive && (
          <div
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.9rem',
              fontWeight: 600,
              color: 'var(--text-primary)',
              minWidth: 56,
              textAlign: 'center',
            }}
          >
            {formatDuration(duration)}
          </div>
        )}

        {/* Status label */}
        {(isAnalyzing || callStatus === 'generating_summary') && (
          <div className={`status-label ${callStatus}`}>
            {isAnalyzing ? 'Analyzing...' : 'Generating summary...'}
          </div>
        )}

        {/* Status message */}
        {statusMessage && !isAnalyzing && (
          <span className="text-xs text-muted" style={{ maxWidth: 240, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {statusMessage}
          </span>
        )}
      </div>

      {/* Right: start/end buttons */}
      <div className="call-controls-right">
        {callStatus === 'idle' || callStatus === 'ended' ? (
          <button
            id="start-call-btn"
            className="btn btn-primary"
            onClick={() => onStartCall(selectedCustomerId || undefined)}
          >
            Start Call
          </button>
        ) : (
          <>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginRight: 8 }}>
              <div className="live-dot" />
              <span className="text-xs" style={{ color: 'var(--color-danger)', fontWeight: 600 }}>CALL ACTIVE</span>
            </div>
            <button
              id="end-call-btn"
              className="btn btn-danger"
              onClick={onEndCall}
              disabled={callStatus === 'generating_summary'}
            >
              End Call
            </button>
          </>
        )}

        {/* Call ID badge */}
        {callId && (
          <div
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.65rem',
              color: 'var(--text-muted)',
              padding: '3px 6px',
              background: 'var(--color-bg-card)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-sm)',
              maxWidth: 120,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
            title={callId}
          >
            {callId.slice(0, 8)}...
          </div>
        )}
      </div>
    </div>
  );
}
