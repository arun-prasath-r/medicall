import React, { useRef, useEffect } from 'react';
import { MessageBubble } from './MessageBubble';
import { ConfirmationCard } from './ConfirmationCard';
import { EmergencyBanner } from './EmergencyBanner';
import { Sparkles, Stethoscope, Calendar, Clock, Activity } from 'lucide-react';

/**
 * Scrollable conversation panel.
 * Automatically scrolls to the newest message while allowing seamless manual scrolling.
 */
export const ConversationPanel = ({
  messages = [],
  interimTranscript = '',
  isProcessing = false,
  pendingConfirmation = null,
  emergencyGuidance = null,
  isEmergency = false,
  onConfirmProposal,
  onCancelProposal,
  isConfirming = false,
  onReplayMessage,
  onSelectSuggestion,
}) => {
  const panelRef = useRef(null);
  const bottomMarkerRef = useRef(null);
  const userHasScrolledUpRef = useRef(false);

  // Monitor user scroll position to avoid jerking the scroll if user scrolled up to read history
  const handleScroll = () => {
    if (!panelRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = panelRef.current;
    // If within 120px of bottom, consider user "at bottom"
    const atBottom = scrollHeight - scrollTop - clientHeight < 120;
    userHasScrolledUpRef.current = !atBottom;
  };

  // Scroll to bottom when new messages arrive, unless user intentionally scrolled up
  useEffect(() => {
    if (!userHasScrolledUpRef.current && bottomMarkerRef.current) {
      bottomMarkerRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, interimTranscript, isProcessing, pendingConfirmation, isEmergency]);

  const suggestions = [
    { text: 'Find a board-certified cardiologist', icon: Stethoscope },
    { text: 'What appointments do I have scheduled?', icon: Calendar },
    { text: 'I have had a dry cough for 3 days', icon: Activity },
    { text: 'Book an appointment for tomorrow', icon: Clock },
  ];

  const isEmpty = messages.length === 0 && !interimTranscript && !isProcessing;

  return (
    <div
      className="conversation-panel"
      ref={panelRef}
      onScroll={handleScroll}
      role="log"
      aria-live="polite"
    >
      {/* Empty Conversation Welcome State */}
      {isEmpty && (
        <div className="assistant-welcome">
          <div className="welcome-icon-circle">
            <Sparkles size={34} />
          </div>
          <h2 className="welcome-title">How can I help you today?</h2>
          <p className="welcome-desc">
            Speak naturally to find physicians, check real-time availability, schedule consultations,
            or navigate medical symptoms. I am connected live to Medicall's verified clinical directory.
          </p>

          <div className="suggestion-chips">
            {suggestions.map((item, idx) => {
              const Icon = item.icon;
              return (
                <button
                  key={idx}
                  type="button"
                  className="suggestion-chip"
                  onClick={() => onSelectSuggestion && onSelectSuggestion(item.text)}
                >
                  <Icon size={14} />
                  <span>{item.text}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Render Message History */}
      {messages.map((msg, index) => (
        <MessageBubble
          key={msg.id || index}
          message={msg}
          onReplay={onReplayMessage}
        />
      ))}

      {/* Live Interim Transcript Bubble while Patient is Speaking */}
      {interimTranscript && (
        <MessageBubble
          message={{
            role: 'user',
            content: interimTranscript,
            isInterim: true,
            timestamp: new Date().toISOString(),
          }}
        />
      )}

      {/* Loading Indicator while Gemini Generates Response & Executes Tools */}
      {isProcessing && (
        <div className="message-row assistant">
          <div className="message-bubble assistant assistant-typing">
            <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginRight: 4 }}>
              Analyzing symptoms & clinic schedules
            </span>
            <div className="typing-dot" />
            <div className="typing-dot" />
            <div className="typing-dot" />
          </div>
        </div>
      )}

      {/* Interactive Appointment Confirmation Card */}
      {pendingConfirmation && (
        <ConfirmationCard
          proposal={pendingConfirmation}
          onConfirm={onConfirmProposal}
          onCancel={onCancelProposal}
          isExecuting={isConfirming}
        />
      )}

      {/* Persistent Emergency Directives Banner */}
      {isEmergency && (
        <EmergencyBanner guidance={emergencyGuidance} />
      )}

      {/* Anchor for Auto-scroll */}
      <div ref={bottomMarkerRef} style={{ height: 1 }} />
    </div>
  );
};

export default ConversationPanel;

