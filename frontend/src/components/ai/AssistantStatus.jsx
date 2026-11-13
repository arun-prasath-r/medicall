import React from 'react';
import { Sparkles, Shield, Wifi } from 'lucide-react';

/**
 * Header status pill displaying AI connection state, model name, and security status.
 */
export const AssistantStatus = ({
  status = 'ready', // 'ready' | 'listening' | 'processing' | 'speaking' | 'confirmation'
  modelName = 'gemini-3.5-flash',
  isConnected = true,
}) => {
  let statusText = 'Ready';
  let dotClass = '';

  if (status === 'listening') {
    statusText = 'Listening...';
    dotClass = 'listening';
  } else if (status === 'processing') {
    statusText = 'Gemini Thinking...';
    dotClass = 'processing';
  } else if (status === 'speaking') {
    statusText = 'Speaking Response';
  } else if (status === 'confirmation') {
    statusText = 'Awaiting Patient Confirmation';
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
      <div
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.4rem',
          backgroundColor: 'var(--bg-subtle)',
          padding: '0.35rem 0.75rem',
          borderRadius: 'var(--radius-full)',
          fontSize: '0.78rem',
          fontWeight: 600,
          color: 'var(--primary-800)',
          border: '1px solid var(--border-light)',
        }}
      >
        <span className={`assistant-status-dot ${dotClass}`} />
        <span>{statusText}</span>
      </div>

      <div
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.35rem',
          backgroundColor: 'var(--primary-50)',
          padding: '0.35rem 0.65rem',
          borderRadius: 'var(--radius-full)',
          fontSize: '0.72rem',
          fontWeight: 600,
          color: 'var(--primary-700)',
          border: '1px solid var(--primary-100)',
        }}
        title="Powered by Google Gemini Generative AI"
      >
        <Sparkles size={12} />
        <span>{modelName}</span>
      </div>

      <div
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.3rem',
          fontSize: '0.72rem',
          color: 'var(--text-muted)',
        }}
        title="Encrypted with JWT Session Authentication"
      >
        <Shield size={12} color="var(--success)" />
        <span>HIPAA / JWT Secured</span>
      </div>
    </div>
  );
};

export default AssistantStatus;

