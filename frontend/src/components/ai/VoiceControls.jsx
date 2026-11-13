import React from 'react';
import { Volume2, VolumeX, Square, RotateCcw, Gauge } from 'lucide-react';

/**
 * Control bar for text-to-speech audio playback and voice parameters:
 * - Mute / Unmute
 * - Stop current speech
 * - Replay last assistant response
 * - Speed rate selector (0.9x, 1.0x, 1.2x)
 */
export const VoiceControls = ({
  isSpeaking,
  isMuted,
  rate,
  onToggleMute,
  onStop,
  onReplay,
  onChangeRate,
  canReplay,
}) => {
  const rates = [0.9, 1.0, 1.2];

  const handleNextRate = () => {
    const currentIndex = rates.indexOf(rate);
    const nextIndex = (currentIndex + 1) % rates.length;
    onChangeRate(rates[nextIndex]);
  };

  return (
    <div className="voice-controls-group">
      {/* Mute / Unmute Toggle */}
      <button
        type="button"
        className={`icon-control-btn ${isMuted ? 'active' : ''}`}
        onClick={onToggleMute}
        title={isMuted ? 'Unmute voice responses' : 'Mute voice responses'}
        aria-label={isMuted ? 'Unmute voice responses' : 'Mute voice responses'}
      >
        {isMuted ? <VolumeX size={15} /> : <Volume2 size={15} />}
        <span>{isMuted ? 'Muted' : 'Voice On'}</span>
      </button>

      {/* Stop Speaking Button (visible when actively vocalizing) */}
      {isSpeaking && (
        <button
          type="button"
          className="icon-control-btn active"
          onClick={onStop}
          title="Stop reading aloud"
          aria-label="Stop reading aloud"
          style={{ color: '#dc2626', borderColor: '#fca5a5' }}
        >
          <Square size={13} fill="#dc2626" />
          <span>Stop</span>
        </button>
      )}

      {/* Replay Last Response Button */}
      <button
        type="button"
        className="icon-control-btn"
        onClick={onReplay}
        disabled={!canReplay || isSpeaking}
        title="Replay last assistant response"
        aria-label="Replay last assistant response"
      >
        <RotateCcw size={14} />
        <span>Replay</span>
      </button>

      {/* Speech Speed Toggle */}
      <button
        type="button"
        className="icon-control-btn"
        onClick={handleNextRate}
        title="Cycle speech speed"
        aria-label={`Current speech speed ${rate}x. Click to change.`}
      >
        <Gauge size={14} />
        <span>{rate}x</span>
      </button>
    </div>
  );
};

export default VoiceControls;

