/**
 * SummaryModal — post-call summary displayed after call ends.
 */
import type { CallSummary } from '../types';

interface Props {
  summary: CallSummary;
  callId: string;
  onClose: () => void;
  onNewCall: () => void;
}

export function SummaryModal({ summary, callId, onClose, onNewCall }: Props) {
  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal-box">
        <div className="modal-header">
          <div>
            <div className="modal-title">Call Summary</div>
            <div className="text-xs text-muted" style={{ marginTop: 2 }}>
              Call ID: {callId.slice(0, 8)}...
              {summary.escalated && (
                <span
                  style={{
                    marginLeft: 8,
                    color: 'var(--color-danger)',
                    fontWeight: 600,
                  }}
                >
                  ESCALATED
                </span>
              )}
            </div>
          </div>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          {/* Issue */}
          <div className="summary-section">
            <div className="summary-label">Customer Issue</div>
            <div className="summary-value">{summary.issue}</div>
          </div>

          <div className="divider" />

          {/* Intent & Sentiment row */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div className="summary-section">
              <div className="summary-label">Primary Intent</div>
              <div className="summary-value" style={{ textTransform: 'capitalize' }}>
                {summary.intent?.replace(/_/g, ' ')}
              </div>
            </div>
            <div className="summary-section">
              <div className="summary-label">Customer Sentiment</div>
              <div className={`sentiment-pill ${summary.customer_sentiment_overall?.toLowerCase()}`}
                   style={{ marginTop: 2 }}>
                {summary.customer_sentiment_overall}
              </div>
            </div>
          </div>

          <div className="divider" />

          {/* Resolution */}
          <div className="summary-section">
            <div className="summary-label">Resolution</div>
            <div className="summary-value">{summary.resolution}</div>
          </div>

          {/* Actions taken */}
          {summary.actions_taken?.length > 0 && (
            <div className="summary-section">
              <div className="summary-label">Actions Taken</div>
              <ul className="summary-list">
                {summary.actions_taken.map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Key information */}
          {summary.key_information?.length > 0 && (
            <div className="summary-section">
              <div className="summary-label">Key Information</div>
              <ul className="summary-list">
                {summary.key_information.map((info, i) => (
                  <li key={i}>{info}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="divider" />

          {/* Follow-up */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div className="summary-section">
              <div className="summary-label">Follow-up Required</div>
              <div className="summary-value" style={{
                color: summary.follow_up_required ? 'var(--color-warning)' : 'var(--color-success)',
                fontWeight: 600,
              }}>
                {summary.follow_up_required ? 'Yes' : 'No'}
              </div>
            </div>
            <div className="summary-section">
              <div className="summary-label">Escalated</div>
              <div className="summary-value" style={{
                color: summary.escalated ? 'var(--color-danger)' : 'var(--color-success)',
                fontWeight: 600,
              }}>
                {summary.escalated ? 'Yes' : 'No'}
              </div>
            </div>
          </div>

          {summary.follow_up_description && (
            <div className="summary-section">
              <div className="summary-label">Follow-up Action</div>
              <div className="summary-value">{summary.follow_up_description}</div>
            </div>
          )}

          {summary.escalation_reason && (
            <div className="summary-section">
              <div className="summary-label">Escalation Reason</div>
              <div className="summary-value" style={{ color: 'var(--color-danger)' }}>
                {summary.escalation_reason}
              </div>
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn btn-ghost" onClick={onClose}>Close</button>
          <button className="btn btn-primary" onClick={onNewCall}>New Call</button>
        </div>
      </div>
    </div>
  );
}
