import React from 'react';
import { Mic, MicOff, Loader2, Volume2, AlertCircle } from 'lucide-react';

/**
 * Large circular microphone button with multi-state visual indicators:
 * - Idle: Ready for voice input
 * - Listening: Pulsing red active speech capture
 * - Processing: Spinning amber loader while Gemini processes tools
 * - Speaking: Green pulsing waves while TTS vocalizes response
 * - Permission-Denied: Mic off with informative tooltip
 * - Unsupported: Browser unsupported alert
 */
export const MicrophoneButton = ({
  isListening,
  isProcessing,
  isSpeaking,
  permissionStatus,
  isSupported,
  onClick,
  disabled,
}) => {
  // Determine primary state
  let stateClass = 'idle';
  let buttonLabel = 'Tap to speak';
  let IconComponent = Mic;

  if (!isSupported) {
    stateClass = 'unsupported';
    buttonLabel = 'Voice unsupported';
    IconComponent = AlertCircle;
  } else if (permissionStatus === 'denied') {
    stateClass = 'error';
    buttonLabel = 'Microphone blocked';
    IconComponent = MicOff;
  } else if (isProcessing) {
    stateClass = 'processing';
    buttonLabel = 'Processing with Gemini...';
    IconComponent = Loader2;
  } else if (isSpeaking) {
    stateClass = 'speaking';
    buttonLabel = 'Speaking... Tap to stop';
    IconComponent = Volume2;
  } else if (isListening) {
    stateClass = 'listening';
    buttonLabel = 'Listening... Tap when done';
    IconComponent = Mic;
  }

  return (
    <div className="mic-section">
      <button
        type="button"
        className={`mic-button ${stateClass}`}
        onClick={onClick}
        disabled={disabled || !isSupported}
        aria-label={buttonLabel}
        title={buttonLabel}
      >
        <div className="mic-pulse-ring" />
        <IconComponent
          size={32}
          className={isProcessing ? 'animate-spin' : ''}
          style={isProcessing ? { animation: 'spin 1s linear infinite' } : {}}
        />
      </button>

      <span className="mic-status-label">
        {stateClass === 'listening' && (
          <span
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              backgroundColor: '#ef4444',
              display: 'inline-block',
            }}
          />
        )}
        {buttonLabel}
      </span>
    </div>
  );
};

export default MicrophoneButton;

