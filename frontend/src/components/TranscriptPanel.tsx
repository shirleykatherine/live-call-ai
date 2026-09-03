/**
 * TranscriptPanel — displays the live conversation with real-time updates.
 */
import { useEffect, useRef, useState } from 'react';
import type { TranscriptEntry } from '../types';

interface Props {
  transcript: TranscriptEntry[];
  isCallActive: boolean;
  onSend: (speaker: 'customer' | 'agent', text: string) => void;
  disabled: boolean;
}

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  } catch {
    return '';
  }
}

export function TranscriptPanel({ transcript, isCallActive, onSend, disabled }: Props) {
  const [text, setText] = useState('');
  const [speaker, setSpeaker] = useState<'customer' | 'agent'>('customer');
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [transcript]);

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(speaker, trimmed);
    setText('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="transcript-panel">
      <div className="transcript-header">
        <span className="transcript-title">Live Transcript</span>
        {isCallActive && (
          <div className="live-indicator">
            <div className="live-dot" />
            LIVE
          </div>
        )}
        <span className="text-xs text-muted" style={{ marginLeft: 'auto', marginRight: 8 }}>
          {transcript.length} turns
        </span>
      </div>

      <div className="transcript-body">
        {transcript.length === 0 && (
          <div className="transcript-empty">
            <div className="transcript-empty-icon">💬</div>
            <span>Conversation will appear here in real time.</span>
            <span className="text-xs text-muted">Start the call and type a message below.</span>
          </div>
        )}

        {transcript.map((entry, idx) => (
          <div key={entry.id || idx} className={`message-row ${entry.speaker}`}>
            {entry.speaker !== 'system' && (
              <div className={`message-avatar ${entry.speaker}`}>
                {entry.speaker === 'customer' ? 'C' : 'A'}
              </div>
            )}
            <div className="message-content">
              <div className="message-meta">
                <span className="message-speaker">
                  {entry.speaker === 'customer' ? 'Customer' : entry.speaker === 'agent' ? 'Agent' : ''}
                </span>
                <span className="message-time">{formatTime(entry.timestamp)}</span>
              </div>
              <div className="message-bubble">{entry.text}</div>
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="input-area">
        <div className="input-row">
          <div className="speaker-toggle">
            <button
              className={`speaker-btn ${speaker === 'customer' ? 'active customer' : ''}`}
              onClick={() => setSpeaker('customer')}
            >
              Customer
            </button>
            <button
              className={`speaker-btn ${speaker === 'agent' ? 'active agent' : ''}`}
              onClick={() => setSpeaker('agent')}
            >
              Agent
            </button>
          </div>
          <textarea
            className="text-input"
            placeholder={isCallActive ? 'Type message and press Enter...' : 'Start a call to begin'}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            rows={1}
          />
          <button className="send-btn" onClick={handleSend} disabled={disabled || !text.trim()}>
            Send
          </button>
        </div>
        <div className="stt-hint">
          <span>Press <kbd style={{ fontFamily: 'monospace', fontSize: '0.7rem', padding: '1px 4px', background: 'var(--color-bg-card)', border: '1px solid var(--color-border)', borderRadius: 3 }}>Enter</kbd> to send</span>
          <span style={{ color: 'var(--color-border)', fontSize: '0.8rem' }}>|</span>
          <span>Shift+Enter for new line</span>
          {isCallActive && (
            <>
              <span style={{ color: 'var(--color-border)', fontSize: '0.8rem' }}>|</span>
              <span style={{ color: 'var(--color-success)' }}>AI analysis active</span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
