import React from 'react';
import { Volume2, User, HeartPulse, Clock } from 'lucide-react';

/**
 * Single conversation message bubble.
 * Formats user vs assistant messages with timestamps, replay actions, and clinical notices.
 */
export const MessageBubble = ({
  message,
  onReplay,
  isSpeakingThis,
}) => {
  const isUser = message.role === 'user';
  const isInterim = message.isInterim;

  const formattedTime = message.timestamp
    ? new Date(message.timestamp).toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      })
    : '';

  return (
    <div className={`message-row ${isUser ? 'user' : 'assistant'}`}>
      <div
        className={`message-bubble ${
          isUser ? 'user' : 'assistant'
        } ${isInterim ? 'interim' : ''}`}
      >
        <div className="message-header">
          {isUser ? (
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <User size={13} />
              You
            </span>
          ) : (
            <span className="assistant-header-meta">
              <HeartPulse size={14} color="var(--primary-600)" />
              Medicall AI Assistant
            </span>
          )}

          {formattedTime && (
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              <Clock size={11} />
              {formattedTime}
            </span>
          )}
        </div>

        {/* Message Content */}
        <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
          {message.content}
        </div>

        {/* Assistant Actions & Disclaimer */}
        {!isUser && !isInterim && (
          <>
            {onReplay && (
              <div className="message-actions">
                <button
                  type="button"
                  className="message-action-btn"
                  onClick={() => onReplay(message.content)}
                  title="Read message aloud"
                >
                  <Volume2 size={13} />
                  <span>{isSpeakingThis ? 'Replaying...' : 'Listen'}</span>
                </button>
              </div>
            )}

            {message.disclaimer && (
              <div className="clinical-disclaimer-pill">
                ℹ️ {message.disclaimer}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default MessageBubble;

