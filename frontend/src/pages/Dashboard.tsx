/**
 * Dashboard — main agent cockpit page.
 * Assembles all components and connects them to the call session hook.
 */
import { useState } from 'react';
import { useCallSession } from '../hooks/useCallSession';
import { TranscriptPanel } from '../components/TranscriptPanel';
import { CopilotPanel } from '../components/CopilotPanel';
import { CustomerInfo } from '../components/CustomerInfo';
import { CallControls } from '../components/CallControls';
import { SummaryModal } from '../components/SummaryModal';

export function Dashboard() {
  const {
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
    isCallActive,
  } = useCallSession();

  const [showSummary, setShowSummary] = useState(false);
  const [prevCallId, setPrevCallId] = useState<string | null>(null);

  // Show summary modal when call ends
  if (callStatus === 'ended' && summary && !showSummary && callId !== prevCallId) {
    setShowSummary(true);
    setPrevCallId(callId);
  }

  const handleNewCall = () => {
    setShowSummary(false);
    startCall(selectedCustomerId || undefined);
  };

  const isAnalyzing = callStatus === 'analyzing';

  return (
    <div className="app-layout">
      {/* Header */}
      <header className="app-header">
        <div className="app-header-brand">
          <div className="brand-dot" />
          Live Call Co-pilot
        </div>

        <div className="app-header-center">
          {callStatus === 'active' && (
            <div className="live-indicator">
              <div className="live-dot" />
              LIVE
            </div>
          )}
          {isAnalyzing && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div className="spinner" />
              <span className="text-xs text-muted">AI Analyzing...</span>
            </div>
          )}
        </div>

        <div className="app-header-right">
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem' }}>
            {new Date().toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
          </span>
          <div className={`conn-indicator`}>
            <div className={`conn-dot ${connectionStatus}`} />
            <span style={{ fontSize: '0.72rem' }}>
              {connectionStatus === 'connected' ? 'Connected' :
               connectionStatus === 'connecting' ? 'Connecting' : 'Offline'}
            </span>
          </div>
        </div>
      </header>

      {/* Main body: transcript | copilot+customer */}
      <div className="dashboard-body">

        {/* Left: transcript + input */}
        <div className="main-panel">
          <TranscriptPanel
            transcript={transcript}
            isCallActive={isCallActive}
            onSend={sendTranscript}
            disabled={!isCallActive}
          />
        </div>

        {/* Right: copilot + customer stacked */}
        <div className="side-panel">
          {/* Customer & order info at top */}
          <CustomerInfo
            customerId={selectedCustomerId || null}
            analysis={analysis}
          />

          {/* AI copilot below */}
          <CopilotPanel
            analysis={analysis}
            isAnalyzing={isAnalyzing}
          />
        </div>

        {/* Bottom bar: call controls */}
        <div className="bottom-bar">
          <CallControls
            callStatus={callStatus}
            connectionStatus={connectionStatus}
            statusMessage={statusMessage}
            selectedCustomerId={selectedCustomerId}
            onSetCustomerId={setSelectedCustomerId}
            onStartCall={startCall}
            onEndCall={endCall}
            callId={callId}
            isAnalyzing={isAnalyzing}
          />
        </div>
      </div>

      {/* Post-call summary modal */}
      {showSummary && summary && callId && (
        <SummaryModal
          summary={summary}
          callId={callId}
          onClose={() => setShowSummary(false)}
          onNewCall={handleNewCall}
        />
      )}
    </div>
  );
}
