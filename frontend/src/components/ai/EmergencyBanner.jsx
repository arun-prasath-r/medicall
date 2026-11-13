import React from 'react';
import { AlertOctagon, PhoneCall, ShieldAlert } from 'lucide-react';

/**
 * High-visibility clinical emergency banner displayed when red-flag life-threatening
 * symptoms are detected. Enforces clinical safety boundaries.
 */
export const EmergencyBanner = ({
  guidance,
  emergencyNumber = '112',
}) => {
  return (
    <div className="emergency-banner" role="alert" aria-live="assertive">
      <div className="emergency-banner-header">
        <AlertOctagon size={24} />
        <span>CRITICAL MEDICAL EMERGENCY DIRECTIVE</span>
      </div>

      <div className="emergency-banner-body">
        {guidance ? (
          <p style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{guidance}</p>
        ) : (
          <p style={{ margin: 0 }}>
            Potential life-threatening symptoms detected. Please <strong>STOP</strong> using online
            appointment scheduling and call emergency services immediately or proceed to the
            nearest emergency room.
          </p>
        )}
      </div>

      <div className="emergency-banner-actions">
        <a
          href={`tel:${emergencyNumber}`}
          className="emergency-call-btn"
          aria-label={`Call Emergency Services ${emergencyNumber}`}
        >
          <PhoneCall size={18} />
          <span>Call Emergency ({emergencyNumber})</span>
        </a>

        <div className="emergency-disclaimer-note">
          <ShieldAlert size={14} style={{ display: 'inline', marginRight: 4 }} />
          Medicall AI is an informational scheduling assistant and <strong>cannot dispatch emergency medical responders</strong>.
        </div>
      </div>
    </div>
  );
};

export default EmergencyBanner;

