import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { appointmentService } from '../services/appointmentService';
import { availabilityService } from '../services/availabilityService';
import { RescheduleModal } from '../components/appointment/RescheduleModal';
import { 
  Calendar, 
  Clock, 
  Stethoscope, 
  AlertCircle, 
  CheckCircle2, 
  XCircle, 
  RefreshCw,
  PlusCircle,
  FileText,
  Filter,
  ArrowRight
} from 'lucide-react';
import { 
  formatReadableDate, 
  formatReadableDateTime, 
  format12HourTime,
  toLocalDateString
} from '../utils/dateTime';
import { formatApiError } from '../utils/errorUtils';

export const PatientAppointmentsPage = () => {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Tab Filtering: 'ALL' | 'UPCOMING' | 'COMPLETED' | 'CANCELLED'
  const [activeTab, setActiveTab] = useState('ALL');

  // Cancel Modal State
  const [cancellingAppt, setCancellingAppt] = useState(null);
  const [cancelReason, setCancelReason] = useState('');
  const [cancelLoading, setCancelLoading] = useState(false);

  // Reschedule Modal State
  const [reschedulingAppt, setReschedulingAppt] = useState(null);
  const [availableSlots, setAvailableSlots] = useState([]);
  const [slotsLoading, setSlotsLoading] = useState(false);
  const [rescheduleSubmitting, setRescheduleSubmitting] = useState(false);
  const [rescheduleError, setRescheduleError] = useState('');

  const loadAppointments = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await appointmentService.getMyAppointments();
      setAppointments(data || []);
    } catch (err) {
      console.error('Error loading appointments:', err);
      setError(formatApiError(err, 'Could not retrieve appointments. Please verify connection to backend.'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAppointments();
  }, []);

  // Filter appointments according to activeTab
  const filteredAppointments = useMemo(() => {
    if (activeTab === 'UPCOMING') {
      return appointments.filter(
        (a) => a.status === 'SCHEDULED' || a.status === 'RESCHEDULED'
      );
    }
    if (activeTab === 'COMPLETED') {
      return appointments.filter((a) => a.status === 'COMPLETED');
    }
    if (activeTab === 'CANCELLED') {
      return appointments.filter(
        (a) => a.status === 'CANCELLED_PATIENT' || a.status === 'CANCELLED_DOCTOR'
      );
    }
    return appointments;
  }, [appointments, activeTab]);

  // Tab counts
  const counts = useMemo(() => {
    return {
      all: appointments.length,
      upcoming: appointments.filter((a) => a.status === 'SCHEDULED' || a.status === 'RESCHEDULED').length,
      completed: appointments.filter((a) => a.status === 'COMPLETED').length,
      cancelled: appointments.filter((a) => a.status === 'CANCELLED_PATIENT' || a.status === 'CANCELLED_DOCTOR').length,
    };
  }, [appointments]);

  // Handle Cancel
  const handleConfirmCancel = async (e) => {
    e.preventDefault();
    if (!cancellingAppt || cancelLoading) return;
    setCancelLoading(true);
    setError('');
    try {
      await appointmentService.cancelAppointment(cancellingAppt.id, cancelReason);
      setSuccessMsg(`Appointment ${cancellingAppt.appointment_reference} cancelled successfully.`);
      setCancellingAppt(null);
      setCancelReason('');
      await loadAppointments();
    } catch (err) {
      console.error('Error cancelling appointment:', err);
      setError(formatApiError(err, 'Cancellation failed.'));
    } finally {
      setCancelLoading(false);
    }
  };

  // Open Reschedule Modal & Fetch open slots for doctor
  const openRescheduleModal = async (appt) => {
    setReschedulingAppt(appt);
    setRescheduleError('');
    setSlotsLoading(true);
    try {
      const todayStr = toLocalDateString(new Date());
      const future = new Date();
      future.setDate(future.getDate() + 60);
      const futureStr = toLocalDateString(future);

      const slots = await availabilityService.getDoctorAvailability(
        appt.doctor_id,
        todayStr,
        futureStr,
        'AVAILABLE'
      );
      setAvailableSlots(slots || []);
    } catch (err) {
      console.error('Error fetching slots for reschedule:', err);
      setRescheduleError(formatApiError(err, 'Could not fetch open availability slots for this practitioner.'));
    } finally {
      setSlotsLoading(false);
    }
  };

  // Handle Reschedule Submission
  const handleConfirmReschedule = async (appointmentId, newSlotId) => {
    setRescheduleSubmitting(true);
    setRescheduleError('');
    try {
      await appointmentService.rescheduleAppointment(appointmentId, newSlotId);
      setSuccessMsg('Your consultation has been rescheduled successfully.');
      setReschedulingAppt(null);
      await loadAppointments();
    } catch (err) {
      console.error('Error rescheduling appointment:', err);
      const msg = formatApiError(
        err,
        'Rescheduling failed. The selected slot may have just been reserved.'
      );
      setRescheduleError(msg);
    } finally {
      setRescheduleSubmitting(false);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'SCHEDULED':
        return <span className="badge badge-success">Scheduled</span>;
      case 'RESCHEDULED':
        return <span className="badge badge-info" style={{ backgroundColor: 'var(--info-bg)', color: 'var(--info)', borderColor: 'var(--info-border)' }}>Rescheduled</span>;
      case 'COMPLETED':
        return <span className="badge badge-neutral">Completed</span>;
      case 'CANCELLED_PATIENT':
        return <span className="badge badge-danger">Cancelled by Patient</span>;
      case 'CANCELLED_DOCTOR':
        return <span className="badge badge-danger">Cancelled by Doctor</span>;
      default:
        return <span className="badge badge-neutral">{status}</span>;
    }
  };

  return (
    <div className="page-wrapper">
      <div className="container">
        {/* Header Title & Action */}
        <div className="appointments-page-header">
          <div>
            <span className="badge badge-neutral" style={{ marginBottom: '0.4rem' }}>
              Patient Portal
            </span>
            <h2>My Appointments</h2>
            <p className="page-header-subtext">
              View scheduled medical consultations, reschedule times with 12-hour slots, and manage records.
            </p>
          </div>
          <Link to="/doctors" className="btn btn-primary btn-sm" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <PlusCircle size={17} />
            <span>Book New Appointment</span>
          </Link>
        </div>

        {/* Success Alert Banner */}
        {successMsg && (
          <div className="alert-banner alert-success" style={{ marginBottom: '1.5rem' }}>
            <CheckCircle2 size={18} />
            <div style={{ flex: 1 }}>{successMsg}</div>
            <button onClick={() => setSuccessMsg('')} className="alert-dismiss-btn">&times;</button>
          </div>
        )}

        {/* Error Alert Banner */}
        {error && (
          <div className="alert-banner alert-danger" style={{ marginBottom: '1.5rem' }}>
            <AlertCircle size={18} />
            <div style={{ flex: 1 }}>{String(error)}</div>
            <button onClick={() => setError('')} className="alert-dismiss-btn">&times;</button>
          </div>
        )}

        {/* Filter Tabs Bar */}
        <div className="appointments-filter-tabs">
          <button
            type="button"
            className={`tab-btn ${activeTab === 'ALL' ? 'is-active' : ''}`}
            onClick={() => setActiveTab('ALL')}
          >
            <span>All</span>
            <span className="tab-pill-count">{counts.all}</span>
          </button>
          <button
            type="button"
            className={`tab-btn ${activeTab === 'UPCOMING' ? 'is-active' : ''}`}
            onClick={() => setActiveTab('UPCOMING')}
          >
            <span>Upcoming</span>
            <span className="tab-pill-count">{counts.upcoming}</span>
          </button>
          <button
            type="button"
            className={`tab-btn ${activeTab === 'COMPLETED' ? 'is-active' : ''}`}
            onClick={() => setActiveTab('COMPLETED')}
          >
            <span>Completed</span>
            <span className="tab-pill-count">{counts.completed}</span>
          </button>
          <button
            type="button"
            className={`tab-btn ${activeTab === 'CANCELLED' ? 'is-active' : ''}`}
            onClick={() => setActiveTab('CANCELLED')}
          >
            <span>Cancelled</span>
            <span className="tab-pill-count">{counts.cancelled}</span>
          </button>
        </div>

        {/* Cancellation Modal */}
        {cancellingAppt && (
          <div className="modal-overlay">
            <div className="modal-content" style={{ maxWidth: '480px' }}>
              <div className="modal-header">
                <h3>Cancel Appointment</h3>
                <button
                  type="button"
                  onClick={() => setCancellingAppt(null)}
                  className="modal-close-btn"
                  disabled={cancelLoading}
                >
                  &times;
                </button>
              </div>
              <form onSubmit={handleConfirmCancel}>
                <div className="modal-body">
                  <p style={{ fontSize: '0.92rem', color: 'var(--text-body)', marginBottom: '1rem' }}>
                    Are you sure you want to cancel appointment <strong>{cancellingAppt.appointment_reference}</strong> with <strong>{cancellingAppt.doctor_name}</strong>?
                  </p>
                  <div className="cancel-notice-box">
                    <AlertCircle size={16} color="var(--danger)" />
                    <span>
                      Cancelling will immediately return this consultation slot back to Dr. {cancellingAppt.doctor_name}'s calendar for other patients.
                    </span>
                  </div>
                  <div className="form-group" style={{ marginTop: '1.25rem' }}>
                    <label className="form-label">Reason for Cancellation (Optional)</label>
                    <textarea
                      className="form-textarea"
                      rows={2}
                      placeholder="e.g. Schedule conflict, feeling better, need alternative date..."
                      value={cancelReason}
                      onChange={(e) => setCancelReason(e.target.value)}
                    />
                  </div>
                </div>
                <div className="modal-footer">
                  <button
                    type="button"
                    onClick={() => setCancellingAppt(null)}
                    className="btn btn-outline btn-sm"
                    disabled={cancelLoading}
                  >
                    Keep Appointment
                  </button>
                  <button
                    type="submit"
                    className="btn btn-danger btn-sm"
                    disabled={cancelLoading}
                  >
                    {cancelLoading ? 'Cancelling...' : 'Confirm Cancellation'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Reschedule Modal (Integrated Step-by-Step Calendar & 12-Hour Slot Picker) */}
        {reschedulingAppt && (
          <RescheduleModal
            appointment={reschedulingAppt}
            availableSlots={availableSlots}
            loading={slotsLoading}
            submitting={rescheduleSubmitting}
            error={rescheduleError}
            onClose={() => setReschedulingAppt(null)}
            onConfirmReschedule={handleConfirmReschedule}
          />
        )}

        {/* Main Appointments List View */}
        {loading ? (
          <div className="appointments-loading-state">
            <div className="animate-spin modal-spinner" />
            <p>Loading your medical consultation records...</p>
          </div>
        ) : filteredAppointments.length === 0 ? (
          <div className="card appointments-empty-card">
            <Calendar size={48} className="empty-calendar-icon" />
            <h3>No Appointments in "{activeTab.toLowerCase()}"</h3>
            <p>
              {activeTab === 'ALL'
                ? 'You have not booked any consultations yet. Explore verified medical specialists and reserve an open slot.'
                : `You currently have no ${activeTab.toLowerCase()} appointments.`}
            </p>
            <Link to="/doctors" className="btn btn-primary btn-sm">
              Explore Doctors
            </Link>
          </div>
        ) : (
          <div className="appointments-list-container">
            {filteredAppointments.map((appt) => {
              const isScheduled = appt.status === 'SCHEDULED' || appt.status === 'RESCHEDULED';
              const isCompleted = appt.status === 'COMPLETED';

              return (
                <div key={appt.id} className="card appointment-item-card">
                  <div className="appointment-card-header">
                    <div className="appointment-provider-meta">
                      <div className="provider-avatar">
                        <Stethoscope size={20} />
                      </div>
                      <div>
                        <div className="appointment-badges-row">
                          {getStatusBadge(appt.status)}
                          <span className="appointment-reference-code">
                            Ref: {appt.appointment_reference}
                          </span>
                        </div>
                        <h3 className="provider-name">
                          {appt.doctor_name || 'Practitioner Consultation'}
                        </h3>
                        <span className="provider-specialty">
                          {appt.doctor_specialty || 'General Practice'}
                        </span>
                      </div>
                    </div>

                    <div className="appointment-datetime-block">
                      <div className="datetime-highlight">
                        <Clock size={16} />
                        <span>{formatReadableDateTime(appt.appointment_datetime)}</span>
                      </div>
                      <span className="booked-timestamp">
                        Booked on {formatReadableDate(appt.created_at)}
                      </span>
                    </div>
                  </div>

                  {/* Chief Complaint / Notes Body */}
                  <div className="appointment-complaint-box">
                    <div className="complaint-item">
                      <strong className="complaint-label">Chief Complaint:</strong>
                      <span className="complaint-text">{appt.chief_complaint}</span>
                    </div>
                    {appt.patient_notes && (
                      <div className="complaint-item" style={{ marginTop: '0.4rem' }}>
                        <strong className="complaint-label">Patient Notes:</strong>
                        <span className="complaint-text">{appt.patient_notes}</span>
                      </div>
                    )}
                    {appt.cancellation_reason && (
                      <div className="cancellation-reason-text">
                        <strong>Cancellation Reason:</strong> {appt.cancellation_reason}
                      </div>
                    )}
                  </div>

                  {/* Card Actions Footer */}
                  <div className="appointment-card-actions">
                    {isScheduled && (
                      <div className="action-buttons-group">
                        <button
                          type="button"
                          onClick={() => openRescheduleModal(appt)}
                          className="btn btn-outline btn-sm action-btn"
                        >
                          <RefreshCw size={14} />
                          <span>Reschedule Time</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => setCancellingAppt(appt)}
                          className="btn btn-danger btn-sm action-btn"
                        >
                          <XCircle size={14} />
                          <span>Cancel Consultation</span>
                        </button>
                      </div>
                    )}

                    {isCompleted && (
                      <Link to={`/doctors/${appt.doctor_id}`} className="btn btn-outline btn-sm action-btn">
                        <span>Book Follow-up</span>
                        <ArrowRight size={14} />
                      </Link>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
