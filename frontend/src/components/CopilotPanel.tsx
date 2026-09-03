/**
 * CopilotPanel — right-side AI analysis panel.
 * Shows intent, sentiment, NBA, suggested response, knowledge, and tool calls.
 */
import { useState } from 'react';
import type { AgentAnalysis } from '../types';

interface Props {
  analysis: AgentAnalysis | null;
  isAnalyzing: boolean;
}

function intentLabel(intent: string): string {
  return intent.replace(/_/g, ' ');
}

function stageLabel(stage: string): string {
  return stage.replace(/_/g, ' ');
}

function actionLabel(action: string): string {
  return action.replace(/_/g, ' ');
}

export function CopilotPanel({ analysis, isAnalyzing }: Props) {
  const [copiedResponse, setCopiedResponse] = useState(false);

  const copyResponse = () => {
    if (analysis?.suggested_response) {
      navigator.clipboard.writeText(analysis.suggested_response);
      setCopiedResponse(true);
      setTimeout(() => setCopiedResponse(false), 2000);
    }
  };

  if (!analysis && !isAnalyzing) {
    return (
      <div className="copilot-panel">
        <div className="panel-section">
          <div className="panel-section-header">
            <span className="panel-section-title">AI Co-pilot</span>
          </div>
          <div className="empty-state" style={{ padding: '30px 16px' }}>
            <div style={{ fontSize: '1.5rem', marginBottom: 8, opacity: 0.3 }}>AI</div>
            <div>Start a call to activate the AI co-pilot.</div>
            <div className="text-xs text-muted" style={{ marginTop: 4 }}>
              Analysis will appear here in real time.
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="copilot-panel">

      {/* Intent */}
      <div className="panel-section">
        <div className="panel-section-header">
          <span className="panel-section-title">Customer Intent</span>
          {analysis && (
            <span className="stage-badge">{stageLabel(analysis.conversation_stage)}</span>
          )}
        </div>
        {isAnalyzing && !analysis ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div className="spinner" />
            <span className="text-sm text-muted">Analyzing...</span>
          </div>
        ) : analysis ? (
          <>
            <div className="intent-badge">{intentLabel(analysis.intent)}</div>
            <div className="confidence-bar" style={{ marginTop: 8 }}>
              <div
                className="confidence-fill"
                style={{ width: `${Math.round(analysis.intent_confidence * 100)}%` }}
              />
            </div>
            <div className="text-xs text-muted" style={{ marginTop: 4 }}>
              Confidence: {Math.round(analysis.intent_confidence * 100)}%
            </div>
            {analysis.key_entities.length > 0 && (
              <div style={{ marginTop: 8 }}>
                {analysis.key_entities.map((e, i) => (
                  <span key={i} className="entity-tag">{e}</span>
                ))}
              </div>
            )}
          </>
        ) : null}
      </div>

      {/* Sentiment */}
      <div className="panel-section">
        <div className="panel-section-header">
          <span className="panel-section-title">Sentiment</span>
        </div>
        {analysis ? (
          <>
            <div className={`sentiment-pill ${analysis.sentiment.toLowerCase()}`}>
              <span>{sentimentIcon(analysis.sentiment)}</span>
              <span>{analysis.sentiment}</span>
            </div>
            <div className="confidence-bar" style={{ marginTop: 8 }}>
              <div
                className="confidence-fill"
                style={{
                  width: `${Math.round(analysis.sentiment_confidence * 100)}%`,
                  background: sentimentColor(analysis.sentiment),
                }}
              />
            </div>
          </>
        ) : (
          <div className="empty-state">—</div>
        )}
      </div>

      {/* Next Best Action */}
      <div className="panel-section">
        <div className="panel-section-header">
          <span className="panel-section-title">Next Best Action</span>
          {isAnalyzing && <div className="spinner" />}
        </div>
        {analysis ? (
          <div className="nba-card">
            <div className="nba-card-header">
              <span className="nba-action">{actionLabel(analysis.next_best_action)}</span>
              <span className={`priority-badge ${analysis.action_priority}`}>
                {analysis.action_priority}
              </span>
            </div>
            {analysis.action_rationale && (
              <div className="nba-rationale">{analysis.action_rationale}</div>
            )}
          </div>
        ) : (
          <div className="empty-state">Waiting for conversation...</div>
        )}
      </div>

      {/* Suggested Response */}
      <div className="panel-section">
        <div className="panel-section-header">
          <span className="panel-section-title">Suggested Response</span>
        </div>
        {analysis?.suggested_response ? (
          <div className="response-card">
            <div className="response-text">"{analysis.suggested_response}"</div>
            <button className="response-copy-btn" onClick={copyResponse}>
              {copiedResponse ? '✓ Copied' : 'Copy to clipboard'}
            </button>
          </div>
        ) : (
          <div className="empty-state">No response suggested yet.</div>
        )}
      </div>

      {/* Tool calls made */}
      {analysis?.tool_calls_made && analysis.tool_calls_made.length > 0 && (
        <div className="panel-section">
          <div className="panel-section-header">
            <span className="panel-section-title">Tools Used</span>
          </div>
          {analysis.tool_calls_made.map((tc, i) => (
            <div key={i} className="tool-call-item">
              <div className="tool-call-name">{tc.tool_name}()</div>
              <div className={`tool-call-status ${tc.success ? 'success' : 'failed'}`}>
                {tc.success ? '✓ OK' : '✗ Failed'}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Retrieved knowledge */}
      {analysis?.retrieved_knowledge && analysis.retrieved_knowledge.length > 0 && (
        <div className="panel-section">
          <div className="panel-section-header">
            <span className="panel-section-title">Relevant Policy</span>
            <span className="text-xs text-muted">{analysis.retrieved_knowledge.length} source{analysis.retrieved_knowledge.length > 1 ? 's' : ''}</span>
          </div>
          {analysis.retrieved_knowledge.map((chunk, i) => (
            <div key={i} className="knowledge-chunk">
              <div className="knowledge-source">
                <span>{chunk.source}</span>
                <span className="knowledge-score">{Math.round(chunk.score * 100)}%</span>
              </div>
              <div className="knowledge-text">{chunk.content}</div>
            </div>
          ))}
        </div>
      )}

      {/* Error state */}
      {analysis?.error && (
        <div className="panel-section">
          <div
            style={{
              padding: '8px 10px',
              background: 'var(--color-danger-dim)',
              border: '1px solid rgba(239,68,68,0.2)',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.75rem',
              color: 'var(--color-danger)',
            }}
          >
            AI error: {analysis.error}
          </div>
        </div>
      )}
    </div>
  );
}

function sentimentIcon(sentiment: string): string {
  const icons: Record<string, string> = {
    positive: '↑',
    neutral: '—',
    frustrated: '!',
    angry: '!!',
    urgent: '⚡',
    satisfied: '✓',
    confused: '?',
  };
  return icons[sentiment.toLowerCase()] || '—';
}

function sentimentColor(sentiment: string): string {
  const colors: Record<string, string> = {
    positive: 'var(--sentiment-positive)',
    neutral: 'var(--sentiment-neutral)',
    frustrated: 'var(--sentiment-frustrated)',
    angry: 'var(--sentiment-angry)',
    urgent: 'var(--sentiment-urgent)',
    satisfied: 'var(--sentiment-satisfied)',
    confused: 'var(--sentiment-confused)',
  };
  return colors[sentiment.toLowerCase()] || 'var(--sentiment-neutral)';
}
