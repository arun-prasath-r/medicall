import React, { useState, useEffect, useMemo } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { doctorService } from '../services/doctorService';
import { availabilityService } from '../services/availabilityService';
import { appointmentService } from '../services/appointmentService';
import { useAuth } from '../hooks/useAuth';
import { AppointmentCalendar } from '../components/appointment/AppointmentCalendar';
import { TimeSlotPicker } from '../components/appointment/TimeSlotPicker';
import {
  Stethoscope,
  Award,
  MapPin,
  Calendar,
  Clock,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
  ArrowLeft,
  ArrowRight,
  Sparkles,
  FileText,
  DollarSign,
  AlertTriangle,
  RotateCcw
} from 'lucide-react';
import {
  formatReadableDate,
  format12HourTime,
  format12HourRange,
  calculateDurationMinutes,
  toLocalDateString
} from '../utils/dateTime';
import { formatApiError } from '../utils/errorUtils';

export const DoctorDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated, isPatient } = useAuth();

  const [doctor, setDoctor] = useState(null);
  const [slots, setSlots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Booking Flow Steps: 1: 'SELECTION' (Date & Time), 2: 'CONFIRM' (Details & Notes), 3: 'SUCCESS' (Receipt)
  const [currentStep, setCurrentStep] = useState(1);

  // Selected State
  const [selectedDate, setSelectedDate] = useState(null);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [chiefComplaint, setChiefComplaint] = useState('');
  const [patientNotes, setPatientNotes] = useState('');

  // Submission States
  const [bookingLoading, setBookingLoading] = useState(false);
  const [bookingError, setBookingError] = useState('');
  const [confirmedAppointment, setConfirmedAppointment] = useState(null);

  // 60-day availability window
  const todayStr = toLocalDateString(new Date());
  const futureDate = new Date();
  futureDate.setDate(futureDate.getDate() + 60);
  const futureStr = toLocalDateString(futureDate);

  useEffect(() => {
    const fetchDoctorAndSlots = async () => {
      setLoading(true);
      setError('');
      try {
        const [docData, slotData] = await Promise.all([
          doctorService.getDoctorById(id),
          availabilityService.getDoctorAvailability(id, todayStr, futureStr, 'AVAILABLE')
        ]);
        setDoctor(docData);
        setSlots(slotData || []);

        // Pre-select first available date if slots exist
        if (slotData && slotData.length > 0) {
          const sortedSlots = [...slotData].sort((a, b) => (a.slot_date > b.slot_date ? 1 : -1));
          setSelectedDate(sortedSlots[0].slot_date);
        } else {
          setSelectedDate(todayStr);
        }
      } catch (err) {
        console.error('Error loading doctor details:', err);
        setError(formatApiError(err, 'Could not retrieve doctor profile. Please verify practitioner ID.'));
      } finally {
        setLoading(false);
      }
    };

    fetchDoctorAndSlots();
  }, [id]);

  // Compute map of { "YYYY-MM-DD": count } for calendar badges
  const availableDatesMap = useMemo(() => {
    const map = {};
    slots.forEach((s) => {
      if (s.status === 'AVAILABLE') {
        map[s.slot_date] = (map[s.slot_date] || 0) + 1;
      }
    });
    return map;
  }, [slots]);

  // Filter slots for selected date
  const slotsForSelectedDate = useMemo(() => {
    if (!selectedDate) return [];
    return slots.filter((s) => s.slot_date === selectedDate);
  }, [slots, selectedDate]);

  const handleDateSelect = (dateStr) => {
    setSelectedDate(dateStr);
    setSelectedSlot(null);
    setBookingError('');
  };

  const handleSlotSelect = (slot) => {
    if (!isAuthenticated) {
      navigate('/login?redirect=' + encodeURIComponent(window.location.pathname));
      return;
    }
    if (!isPatient) {
      setBookingError('Only registered patients can book doctor consultations. Please sign in with a patient account.');
      return;
    }
    setSelectedSlot(slot);
    setBookingError('');
  };

  const handleProceedToReview = () => {
    if (!selectedSlot) {
      setBookingError('Please select an available time slot before continuing.');
      return;
    }
    setBookingError('');
    setCurrentStep(2);
    // Smooth scroll to top of booking card
    window.scrollTo({ top: 200, behavior: 'smooth' });
  };

  const handleConfirmBooking = async (e) => {
    e.preventDefault();
    if (!selectedSlot || !selectedSlot.id) {
      setBookingError('Please select a valid consultation time slot before confirming.');
      return;
    }

    if (!doctor || !doctor.id) {
      setBookingError('Doctor details are missing. Please refresh the page and try again.');
      return;
    }

    const complaintText = chiefComplaint.trim();
    if (complaintText.length < 3) {
      setBookingError('Please describe your chief complaint or symptoms (at least 3 characters).');
      return;
    }

    setBookingLoading(true);
    setBookingError('');

    // Combine any extra patient notes cleanly into complaint payload
    const fullComplaint = patientNotes.trim()
      ? `${complaintText} (Patient Notes: ${patientNotes.trim()})`
      : complaintText;

    try {
      const resp = await appointmentService.bookAppointment({
        doctor_id: doctor.id,
        availability_id: selectedSlot.id,
        chief_complaint: fullComplaint,
      });

      setConfirmedAppointment(resp);
      // Remove newly booked slot from local availability
      setSlots((prev) => prev.filter((s) => s.id !== selectedSlot.id));
      setCurrentStep(3);
    } catch (err) {
      console.error('Booking collision / error:', err);
      const errorMsg = formatApiError(
        err,
        'This consultation slot has just been reserved by another patient. Please choose an alternative time.'
      );
      setBookingError(errorMsg);
      // If 409 conflict, revert to step 1 so patient can pick another slot
      if (err.response?.status === 409) {
        setSlots((prev) => prev.filter((s) => s.id !== selectedSlot.id));
        setSelectedSlot(null);
        setCurrentStep(1);
      }
    } finally {
      setBookingLoading(false);
    }
  };

  const handleResetFlow = () => {
    setCurrentStep(1);
    setSelectedSlot(null);
    setConfirmedAppointment(null);
    setChiefComplaint('');
    setPatientNotes('');
    setBookingError('');
  };

  if (loading) {
    return (
      <div className="page-wrapper" style={{ textAlign: 'center', padding: '5rem 0' }}>
        <div className="animate-spin modal-spinner" style={{ margin: '0 auto 1.5rem auto' }} />
        <h3 style={{ fontSize: '1.25rem', color: 'var(--primary-800)' }}>Loading Doctor Profile</h3>
        <p style={{ color: 'var(--text-muted)' }}>Fetching live appointment slots and clinic details...</p>
      </div>
    );
  }

  if (error || !doctor) {
    return (
      <div className="page-wrapper">
        <div className="container container-narrow">
          <div className="card" style={{ textAlign: 'center', padding: '3.5rem 2rem' }}>
            <AlertCircle size={44} color="var(--danger)" style={{ margin: '0 auto 1rem auto' }} />
            <h3>Doctor Profile Not Found</h3>
            <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>{String(error)}</p>
            <Link to="/doctors" className="btn btn-primary">
              <ArrowLeft size={16} />
              Return to Doctor Directory
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page-wrapper">
      <div className="container">
        {/* Navigation Breadcrumb */}
        <Link
          to="/doctors"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.4rem',
            marginBottom: '1.75rem',
            color: 'var(--text-muted)',
            fontSize: '0.9rem',
            fontWeight: 500
          }}
        >
          <ArrowLeft size={16} />
          <span>Back to All Doctors</span>
        </Link>

        {/* Global Error Banner */}
        {bookingError && (
          <div className="alert-banner alert-danger" style={{ marginBottom: '1.5rem' }}>
            <AlertCircle size={18} />
            <span>{String(bookingError)}</span>
          </div>
        )}

        <div className="doctor-detail-layout">
          {/* LEFT COLUMN: Doctor Dossier Card */}
          <aside className="doctor-profile-sidebar">
            <div className="card doctor-sidebar-card">
              <div className="sidebar-avatar-wrapper">
                <div className="doctor-profile-avatar">
                  {(doctor.first_name?.[0] || 'D')}{(doctor.last_name?.[0] || 'R')}
                </div>
                <h2 className="doctor-profile-name">
                  Dr. {doctor.first_name} {doctor.last_name}
                </h2>
                <span className="doctor-profile-specialty">
                  <Stethoscope size={16} />
                  {doctor.specialty}
                </span>

                <div className="doctor-profile-status-badge">
                  {doctor.is_verified ? (
                    <span className="badge badge-success">
                      <ShieldCheck size={13} />
                      Verified Practitioner
                    </span>
                  ) : (
                    <span className="badge badge-warning">
                      <AlertCircle size={13} />
                      Credential Review Pending
                    </span>
                  )}
                </div>
              </div>

              {/* Consultation Fee Card */}
              <div className="sidebar-fee-card">
                <span className="fee-label">Consultation Fee</span>
                <div className="fee-amount">
                  ${Number(doctor.consultation_fee).toFixed(0)}
                  <span className="fee-period"> / session</span>
                </div>
              </div>

              {/* Clinical Details List */}
              <div className="sidebar-details-list">
                <div className="sidebar-detail-item">
                  <span className="detail-label">Qualifications</span>
                  <div className="detail-value">
                    <Award size={16} className="detail-icon" />
                    <span>{doctor.qualifications}</span>
                  </div>
                </div>

                <div className="sidebar-detail-item">
                  <span className="detail-label">Experience</span>
                  <div className="detail-value">
                    <Clock size={16} className="detail-icon" />
                    <span>{doctor.experience_years} Years Active Practice</span>
                  </div>
                </div>

                {doctor.clinic_address && (
                  <div className="sidebar-detail-item">
                    <span className="detail-label">Clinic Location</span>
                    <div className="detail-value">
                      <MapPin size={16} className="detail-icon" />
                      <span>{doctor.clinic_address}</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Bio Section */}
              {doctor.bio && (
                <div className="sidebar-bio-section">
                  <span className="detail-label">About Practitioner</span>
                  <p className="sidebar-bio-text">{doctor.bio}</p>
                </div>
              )}

              {/* Clinical Emergency Disclaimer */}
              <div className="sidebar-emergency-notice">
                <AlertTriangle size={15} />
                <span>
                  For urgent life-threatening symptoms (e.g. chest pain, severe shortness of breath), call <strong>911</strong> immediately.
                </span>
              </div>
            </div>
          </aside>

          {/* RIGHT COLUMN: Interactive Step-by-Step Appointment Booking Experience */}
          <main className="doctor-booking-main">
            {/* Unverified Doctor Alert */}
            {!doctor.is_verified && (
              <div className="alert-banner alert-warning" style={{ marginBottom: '1.5rem' }}>
                <AlertCircle size={20} />
                <div>
                  <strong>Doctor Credentials Pending Administrative Verification</strong>
                  <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.85rem' }}>
                    Dr. {doctor.last_name}'s state medical license is currently being reviewed. Online slot booking will activate as soon as the profile is verified.
                  </p>
                </div>
              </div>
            )}

            {/* STEP 4 / SUCCESS RECEIPT SCREEN */}
            {currentStep === 3 && confirmedAppointment && (
              <div className="card booking-receipt-card">
                <div className="receipt-success-badge">
                  <CheckCircle2 size={40} />
                </div>
                <h2>Appointment Confirmed!</h2>
                <p className="receipt-subtitle">
                  Your doctor consultation has been securely reserved with PostgreSQL concurrency protection.
                </p>

                <div className="receipt-details-table">
                  <div className="receipt-row">
                    <span className="row-label">Appointment Reference</span>
                    <strong className="row-value highlight-ref">
                      {confirmedAppointment.appointment_reference}
                    </strong>
                  </div>
                  <div className="receipt-row">
                    <span className="row-label">Doctor</span>
                    <span className="row-value">
                      {confirmedAppointment.doctor_name || `Dr. ${doctor.first_name} ${doctor.last_name}`} ({doctor.specialty})
                    </span>
                  </div>
                  <div className="receipt-row">
                    <span className="row-label">Date & Time</span>
                    <span className="row-value font-medium">
                      {formatReadableDate(selectedSlot.slot_date)} &bull; {format12HourTime(selectedSlot.start_time)}
                    </span>
                  </div>
                  <div className="receipt-row">
                    <span className="row-label">Duration</span>
                    <span className="row-value">
                      {calculateDurationMinutes(selectedSlot.start_time, selectedSlot.end_time)} minutes
                    </span>
                  </div>
                  <div className="receipt-row">
                    <span className="row-label">Reason for Visit</span>
                    <span className="row-value">
                      {chiefComplaint || 'General medical consultation'}
                    </span>
                  </div>
                  <div className="receipt-row">
                    <span className="row-label">Consultation Fee</span>
                    <strong className="row-value">
                      ${Number(doctor.consultation_fee).toFixed(2)}
                    </strong>
                  </div>
                </div>

                <div className="receipt-action-buttons">
                  <Link to="/appointments" className="btn btn-primary">
                    <Calendar size={16} />
                    View in My Appointments
                  </Link>
                  <button type="button" onClick={handleResetFlow} className="btn btn-outline">
                    <RotateCcw size={16} />
                    Book Another Slot
                  </button>
                </div>
              </div>
            )}

            {/* STEP 1 & 2: DATE & TIME SELECTION */}
            {currentStep === 1 && (
              <div className="card booking-wizard-card">
                {/* Step Progress Header */}
                <div className="booking-stepper-header">
                  <div className="step-item active">
                    <span className="step-badge">1</span>
                    <div className="step-text">
                      <span className="step-subtitle">Step 1</span>
                      <strong className="step-name">Select Date</strong>
                    </div>
                  </div>
                  <div className="step-divider" />
                  <div className={`step-item ${selectedSlot ? 'active' : ''}`}>
                    <span className="step-badge">2</span>
                    <div className="step-text">
                      <span className="step-subtitle">Step 2</span>
                      <strong className="step-name">Select Time Slot</strong>
                    </div>
                  </div>
                  <div className="step-divider" />
                  <div className="step-item muted">
                    <span className="step-badge">3</span>
                    <div className="step-text">
                      <span className="step-subtitle">Step 3</span>
                      <strong className="step-name">Review & Confirm</strong>
                    </div>
                  </div>
                </div>

                {/* Calendar + Time Slots Split Grid */}
                <div className="booking-selection-grid">
                  {/* Calendar Column */}
                  <div className="booking-calendar-pane">
                    <div className="pane-header">
                      <Calendar size={17} className="pane-icon" />
                      <h4>1. Choose Consultation Date</h4>
                    </div>
                    <AppointmentCalendar
                      selectedDate={selectedDate}
                      onSelectDate={handleDateSelect}
                      availableDatesMap={availableDatesMap}
                    />
                  </div>

                  {/* Time Slots Column */}
                  <div className="booking-time-slots-pane">
                    <div className="pane-header">
                      <Clock size={17} className="pane-icon" />
                      <h4>2. Choose Available Time (12-Hour)</h4>
                    </div>
                    <TimeSlotPicker
                      slots={slotsForSelectedDate}
                      selectedSlot={selectedSlot}
                      onSelectSlot={handleSlotSelect}
                      selectedDate={selectedDate}
                    />
                  </div>
                </div>

                {/* Bottom Action Tray */}
                <div className="booking-action-tray">
                  <div className="action-tray-summary">
                    {selectedSlot ? (
                      <div className="selected-slot-preview">
                        <CheckCircle2 size={18} color="var(--success)" />
                        <div>
                          <span className="preview-heading">Selected Consultation Window:</span>
                          <strong className="preview-time-string">
                            {formatReadableDate(selectedDate)} &bull; {format12HourTime(selectedSlot.start_time)} ({calculateDurationMinutes(selectedSlot.start_time, selectedSlot.end_time)} min)
                          </strong>
                        </div>
                      </div>
                    ) : (
                      <span className="no-slot-selected-tip">
                        Please click an open time slot above to proceed to review.
                      </span>
                    )}
                  </div>

                  <button
                    type="button"
                    onClick={handleProceedToReview}
                    disabled={!selectedSlot || !doctor.is_verified}
                    className="btn btn-primary btn-lg"
                    style={{ minWidth: '220px' }}
                  >
                    <span>Continue to Details</span>
                    <ArrowRight size={18} />
                  </button>
                </div>
              </div>
            )}

            {/* STEP 3: CONSULTATION DETAILS & REVIEW */}
            {currentStep === 2 && selectedSlot && (
              <div className="card booking-wizard-card">
                {/* Stepper Header */}
                <div className="booking-stepper-header">
                  <div className="step-item completed" onClick={() => setCurrentStep(1)} style={{ cursor: 'pointer' }}>
                    <span className="step-badge">&#10003;</span>
                    <div className="step-text">
                      <span className="step-subtitle">Step 1 & 2</span>
                      <strong className="step-name">{formatReadableDate(selectedDate)} &bull; {format12HourTime(selectedSlot.start_time)}</strong>
                    </div>
                  </div>
                  <div className="step-divider" />
                  <div className="step-item active">
                    <span className="step-badge">3</span>
                    <div className="step-text">
                      <span className="step-subtitle">Final Step</span>
                      <strong className="step-name">Review & Confirm</strong>
                    </div>
                  </div>
                </div>

                <form onSubmit={handleConfirmBooking} className="review-confirm-form">
                  {/* Summary Overview Card */}
                  <div className="consultation-summary-box">
                    <h4 className="summary-box-title">Appointment Summary</h4>
                    <div className="summary-box-grid">
                      <div className="summary-item">
                        <span className="label">Healthcare Provider</span>
                        <strong className="value">Dr. {doctor.first_name} {doctor.last_name}</strong>
                        <span className="subvalue">{doctor.specialty}</span>
                      </div>
                      <div className="summary-item">
                        <span className="label">Scheduled Date</span>
                        <strong className="value">{formatReadableDate(selectedDate)}</strong>
                        <span className="subvalue">In-Person / Video Consultation</span>
                      </div>
                      <div className="summary-item">
                        <span className="label">Consultation Time</span>
                        <strong className="value highlight-text">
                          {format12HourRange(selectedSlot.start_time, selectedSlot.end_time)}
                        </strong>
                        <span className="subvalue">{calculateDurationMinutes(selectedSlot.start_time, selectedSlot.end_time)} minutes duration</span>
                      </div>
                      <div className="summary-item">
                        <span className="label">Fee Due at Visit</span>
                        <strong className="value fee">${Number(doctor.consultation_fee).toFixed(2)}</strong>
                        <span className="subvalue">Standard Consultation</span>
                      </div>
                    </div>
                  </div>

                  {/* Patient Clinical Input Fields */}
                  <div className="form-group" style={{ marginTop: '1.5rem' }}>
                    <label className="form-label">
                      Primary Reason for Consultation / Chief Complaint *
                    </label>
                    <textarea
                      className="form-textarea"
                      rows={3}
                      placeholder="Please describe your symptoms, health concern, or purpose for visiting (e.g. routine checkup, persistent headache, prescription review)..."
                      value={chiefComplaint}
                      onChange={(e) => setChiefComplaint(e.target.value)}
                      required
                    />
                    <span className="form-hint" style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      This information helps Dr. {doctor.last_name} prepare for your consultation in advance.
                    </span>
                  </div>

                  <div className="form-group" style={{ marginTop: '1rem' }}>
                    <label className="form-label">Additional Patient Notes (Optional)</label>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="e.g. Previous blood test results available, require wheel-chair access..."
                      value={patientNotes}
                      onChange={(e) => setPatientNotes(e.target.value)}
                    />
                  </div>

                  {/* Safety & Non-Diagnostic Scope Disclaimer */}
                  <div className="booking-safety-disclaimer">
                    <ShieldCheck size={16} className="disclaimer-icon" />
                    <span>
                      <strong>Clinical Practice Notice:</strong> Medicall provides scheduling and preliminary healthcare information. It does not replace emergency clinical judgment. If you suffer acute chest pain or emergency conditions, call emergency services immediately.
                    </span>
                  </div>

                  {/* Form Footer Action Buttons */}
                  <div className="review-footer-buttons">
                    <button
                      type="button"
                      onClick={() => setCurrentStep(1)}
                      className="btn btn-outline"
                      disabled={bookingLoading}
                    >
                      <ArrowLeft size={16} />
                      Back to Date & Time
                    </button>
                    <button
                      type="submit"
                      className="btn btn-primary btn-lg"
                      disabled={bookingLoading}
                    >
                      {bookingLoading ? (
                        <>
                          <div className="animate-spin" style={{ width: '16px', height: '16px', border: '2px solid white', borderTopColor: 'transparent', borderRadius: '50%' }} />
                          <span>Securing Appointment...</span>
                        </>
                      ) : (
                        <>
                          <CheckCircle2 size={18} />
                          <span>Confirm & Book Consultation</span>
                        </>
                      )}
                    </button>
                  </div>
                </form>
              </div>
            )}
          </main>
        </div>
      </div>
    </div>
  );
};
