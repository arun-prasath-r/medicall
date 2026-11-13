import React, { useState } from 'react';
import { 
  Calendar, 
  Clock, 
  User, 
  AlertTriangle, 
  CheckCircle2, 
  XCircle, 
  ArrowRight,
  DollarSign,
  ShieldCheck,
  Loader2
} from 'lucide-react';

/**
 * Dedicated interactive appointment confirmation card for proposals requiring explicit patient consent.
 * Supports:
 * - book_appointment
 * - cancel_appointment
 * - reschedule_appointment
 */
export const ConfirmationCard = ({
  proposal,
  onConfirm,
  onCancel,
  isExecuting = false,
}) => {
  const [errorMessage, setErrorMessage] = useState(null);

  if (!proposal) return null;

  const {
    action,
    confirmation_token,
    doctor_name,
    specialty,
    consultation_fee,
    slot_date,
    slot_time,
    chief_complaint,
    appointment_id,
    reference_code,
    appointment_datetime,
    reason,
    old_date,
    old_time,
    new_date,
    new_time,
    summary,
  } = proposal;

  const isBooking = action === 'book_appointment';
  const isCancellation = action === 'cancel_appointment';
  const isReschedule = action === 'reschedule_appointment';

  const handleConfirmClick = async () => {
    setErrorMessage(null);
    try {
      await onConfirm(confirmation_token, proposal);
    } catch (err) {
      setErrorMessage(err.message || 'Confirmation failed. Please try again.');
    }
  };

  return (
    <div className={`confirmation-card ${isBooking ? 'booking' : isCancellation ? 'cancellation' : 'reschedule'}`}>
      <div className="confirmation-card-header">
        {isBooking && <Calendar size={22} color="var(--primary-700)" />}
        {isCancellation && <AlertTriangle size={22} color="#dc2626" />}
        {isReschedule && <Clock size={22} color="#2563eb" />}

        <div>
          <h4>
            {isBooking && 'Confirm Appointment Booking'}
            {isCancellation && 'Confirm Appointment Cancellation'}
            {isReschedule && 'Confirm Appointment Reschedule'}
          </h4>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Explicit patient authorization required
          </span>
        </div>
      </div>

      {/* Summary Narrative */}
      {summary && (
        <p style={{ fontSize: '0.92rem', color: 'var(--text-body)', marginBottom: '1rem', lineHeight: 1.5 }}>
          {summary}
        </p>
      )}

      {/* Structured Details Grid */}
      <div className="confirmation-detail-grid">
        {doctor_name && (
          <div className="confirmation-detail-item">
            <span className="confirmation-detail-label">Practitioner</span>
            <span className="confirmation-detail-value">{doctor_name}</span>
          </div>
        )}

        {specialty && (
          <div className="confirmation-detail-item">
            <span className="confirmation-detail-label">Specialty</span>
            <span className="confirmation-detail-value">{specialty}</span>
          </div>
        )}

        {isBooking && (
          <>
            <div className="confirmation-detail-item">
              <span className="confirmation-detail-label">Proposed Date</span>
              <span className="confirmation-detail-value">{slot_date}</span>
            </div>
            <div className="confirmation-detail-item">
              <span className="confirmation-detail-label">Proposed Time</span>
              <span className="confirmation-detail-value">{slot_time}</span>
            </div>
            {consultation_fee !== undefined && (
              <div className="confirmation-detail-item">
                <span className="confirmation-detail-label">Consultation Fee</span>
                <span className="confirmation-detail-value">${Number(consultation_fee).toFixed(2)}</span>
              </div>
            )}
            {chief_complaint && (
              <div className="confirmation-detail-item" style={{ gridColumn: '1 / -1' }}>
                <span className="confirmation-detail-label">Reason / Complaint</span>
                <span className="confirmation-detail-value">{chief_complaint}</span>
              </div>
            )}
          </>
        )}

        {isCancellation && (
          <>
            {reference_code && (
              <div className="confirmation-detail-item">
                <span className="confirmation-detail-label">Reference</span>
                <span className="confirmation-detail-value">{reference_code}</span>
              </div>
            )}
            {appointment_datetime && (
              <div className="confirmation-detail-item">
                <span className="confirmation-detail-label">Scheduled For</span>
                <span className="confirmation-detail-value">{appointment_datetime}</span>
              </div>
            )}
            {reason && (
              <div className="confirmation-detail-item" style={{ gridColumn: '1 / -1' }}>
                <span className="confirmation-detail-label">Cancellation Reason</span>
                <span className="confirmation-detail-value">{reason}</span>
              </div>
            )}
          </>
        )}

        {isReschedule && (
          <>
            {reference_code && (
              <div className="confirmation-detail-item">
                <span className="confirmation-detail-label">Reference</span>
                <span className="confirmation-detail-value">{reference_code}</span>
              </div>
            )}
            <div className="confirmation-detail-item">
              <span className="confirmation-detail-label">Current Appointment</span>
              <span className="confirmation-detail-value">{old_date || ''} {old_time || ''}</span>
            </div>
            <div className="confirmation-detail-item">
              <span className="confirmation-detail-label">New Selected Time</span>
              <span className="confirmation-detail-value" style={{ color: 'var(--primary-700)' }}>
                {new_date || slot_date || ''} {new_time || slot_time || ''}
              </span>
            </div>
          </>
        )}
      </div>

      {/* Security Assurance */}
      <div className="confirmation-security-note">
        <ShieldCheck size={14} color="var(--success)" />
        <span>
          Secured with single-use cryptographic token. No changes will be made without pressing confirm.
        </span>
      </div>

      {/* Error Banner if confirmation fails */}
      {errorMessage && (
        <div style={{
          backgroundColor: '#fef2f2',
          border: '1px solid #fecaca',
          borderRadius: 'var(--radius-sm)',
          padding: '0.65rem 0.85rem',
          color: '#991b1b',
          fontSize: '0.85rem',
          marginBottom: '1rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.4rem'
        }}>
          <AlertTriangle size={15} />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Action Buttons */}
      <div className="confirmation-actions">
        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => onCancel(proposal)}
          disabled={isExecuting}
          style={{ fontSize: '0.88rem', padding: '0.55rem 1.15rem' }}
        >
          <XCircle size={16} />
          <span>{isCancellation ? 'Keep Appointment' : 'Decline / Cancel'}</span>
        </button>

        <button
          type="button"
          className="btn btn-primary"
          onClick={handleConfirmClick}
          disabled={isExecuting}
          style={{
            fontSize: '0.88rem',
            padding: '0.55rem 1.25rem',
            backgroundColor: isCancellation ? '#dc2626' : 'var(--primary-700)',
            borderColor: isCancellation ? '#dc2626' : 'var(--primary-700)',
          }}
        >
          {isExecuting ? (
            <>
              <Loader2 size={16} className="animate-spin" style={{ animation: 'spin 1s linear infinite' }} />
              <span>Verifying & Committing...</span>
            </>
          ) : (
            <>
              <CheckCircle2 size={16} />
              <span>
                {isBooking && 'Confirm Booking'}
                {isCancellation && 'Confirm Cancellation'}
                {isReschedule && 'Confirm Rescheduling'}
              </span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default ConfirmationCard;

