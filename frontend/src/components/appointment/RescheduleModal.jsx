import React, { useState, useMemo } from 'react';
import { 
  Calendar, 
  Clock, 
  ArrowRight, 
  AlertCircle, 
  CheckCircle2, 
  X, 
  RefreshCw,
  Stethoscope,
  Info
} from 'lucide-react';
import { AppointmentCalendar } from './AppointmentCalendar';
import { TimeSlotPicker } from './TimeSlotPicker';
import { 
  formatReadableDate, 
  formatReadableDateTime, 
  format12HourTime,
  calculateDurationMinutes,
  toLocalDateString
} from '../../utils/dateTime';

export const RescheduleModal = ({
  appointment,
  availableSlots = [],
  loading = false,
  submitting = false,
  error = '',
  onClose,
  onConfirmReschedule,
}) => {
  // Compute available dates map from availableSlots
  const availableDatesMap = useMemo(() => {
    const map = {};
    availableSlots.forEach((slot) => {
      if (slot.status === 'AVAILABLE') {
        map[slot.slot_date] = (map[slot.slot_date] || 0) + 1;
      }
    });
    return map;
  }, [availableSlots]);

  // First available date or today
  const firstAvailableDate = useMemo(() => {
    const dates = Object.keys(availableDatesMap).sort();
    return dates.length > 0 ? dates[0] : toLocalDateString(new Date());
  }, [availableDatesMap]);

  const [selectedDate, setSelectedDate] = useState(firstAvailableDate);
  const [selectedSlot, setSelectedSlot] = useState(null);

  // Filter slots for the selected date
  const slotsForSelectedDate = useMemo(() => {
    if (!selectedDate) return [];
    return availableSlots.filter((s) => s.slot_date === selectedDate);
  }, [availableSlots, selectedDate]);

  const handleDateChange = (dateStr) => {
    setSelectedDate(dateStr);
    setSelectedSlot(null);
  };

  const handleSlotSelect = (slot) => {
    setSelectedSlot(slot);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!selectedSlot || submitting) return;
    onConfirmReschedule(appointment.id, selectedSlot.id);
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content reschedule-modal-content">
        <div className="modal-header">
          <div className="modal-title-with-badge">
            <RefreshCw size={20} className="modal-title-icon" />
            <div>
              <h3>Reschedule Appointment</h3>
              <span className="modal-subtitle">
                Ref: {appointment.appointment_reference} &bull; Dr. {appointment.doctor_name || 'Practitioner'}
              </span>
            </div>
          </div>
          <button 
            type="button" 
            onClick={onClose} 
            className="modal-close-btn"
            disabled={submitting}
            aria-label="Close"
          >
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body reschedule-modal-body">
            {error && (
              <div className="alert-banner alert-danger">
                <AlertCircle size={18} />
                <span>{String(error)}</span>
              </div>
            )}

            {/* Current Appointment Banner */}
            <div className="reschedule-current-banner">
              <div className="current-banner-header">
                <span className="badge badge-neutral">Current Booking</span>
              </div>
              <div className="current-banner-details">
                <div className="detail-item">
                  <Calendar size={15} />
                  <span>{formatReadableDateTime(appointment.appointment_datetime)}</span>
                </div>
                <div className="detail-item">
                  <Stethoscope size={15} />
                  <span>{appointment.doctor_specialty || 'General Care'}</span>
                </div>
              </div>
            </div>

            {loading ? (
              <div className="reschedule-loading-state">
                <div className="animate-spin modal-spinner" />
                <p>Retrieving real-time calendar availability for Dr. {appointment.doctor_name}...</p>
              </div>
            ) : availableSlots.length === 0 ? (
              <div className="reschedule-empty-state">
                <AlertCircle size={32} color="var(--warning)" />
                <h4>No Alternative Slots Published</h4>
                <p>Dr. {appointment.doctor_name} does not currently have any other available slots published across the next 30 days.</p>
              </div>
            ) : (
              <div className="reschedule-picker-layout">
                {/* Left Column: Calendar Date Selection */}
                <div className="reschedule-col-calendar">
                  <div className="section-step-indicator">
                    <span className="step-number">1</span>
                    <span className="step-title">Select New Date</span>
                  </div>
                  <AppointmentCalendar
                    selectedDate={selectedDate}
                    onSelectDate={handleDateChange}
                    availableDatesMap={availableDatesMap}
                  />
                </div>

                {/* Right Column: Time Slot Picker & Comparison */}
                <div className="reschedule-col-slots">
                  <div className="section-step-indicator">
                    <span className="step-number">2</span>
                    <span className="step-title">Select New Time Slot</span>
                  </div>
                  <TimeSlotPicker
                    slots={slotsForSelectedDate}
                    selectedSlot={selectedSlot}
                    onSelectSlot={handleSlotSelect}
                    selectedDate={selectedDate}
                  />

                  {/* Comparison Summary if slot is selected */}
                  {selectedSlot && (
                    <div className="reschedule-comparison-card">
                      <div className="comparison-title">
                        <CheckCircle2 size={16} color="var(--success)" />
                        <span>Reschedule Confirmation Summary</span>
                      </div>
                      <div className="comparison-grid">
                        <div className="comparison-col before">
                          <span className="col-label">Current:</span>
                          <span className="col-time">{formatReadableDateTime(appointment.appointment_datetime)}</span>
                        </div>
                        <div className="comparison-arrow">
                          <ArrowRight size={18} />
                        </div>
                        <div className="comparison-col after">
                          <span className="col-label">New Proposed Time:</span>
                          <span className="col-time highlight">
                            {formatReadableDate(selectedSlot.slot_date)} &bull; {format12HourTime(selectedSlot.start_time)}
                          </span>
                        </div>
                      </div>
                      <div className="comparison-notice">
                        <Info size={13} />
                        <span>Your previous time slot will be automatically restored to the doctor's calendar.</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="modal-footer">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-outline btn-sm"
              disabled={submitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary btn-sm"
              disabled={submitting || !selectedSlot}
            >
              {submitting ? 'Confirming Reschedule...' : 'Confirm Reschedule'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

