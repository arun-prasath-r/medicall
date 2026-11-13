import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { doctorService } from '../services/doctorService';
import { availabilityService } from '../services/availabilityService';
import { appointmentService } from '../services/appointmentService';
import { 
  Calendar, 
  Clock, 
  User, 
  Plus, 
  AlertCircle, 
  CheckCircle2, 
  ShieldCheck, 
  CalendarPlus, 
  Settings,
  Layers
} from 'lucide-react';
import { formatReadableDateTime, format12HourRange } from '../utils/dateTime';
import { formatApiError } from '../utils/errorUtils';

export const DoctorDashboardPage = () => {
  const { user } = useAuth();
  const doctorId = user?.profile_id;

  const [appointments, setAppointments] = useState([]);
  const [schedules, setSchedules] = useState([]);
  const [doctorProfile, setDoctorProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [statusMsg, setStatusMsg] = useState({ type: '', text: '' });

  // Schedule template modal/form
  const [dayOfWeek, setDayOfWeek] = useState(0); // Monday
  const [startTime, setStartTime] = useState('09:00');
  const [endTime, setEndTime] = useState('17:00');
  const [durationMinutes, setDurationMinutes] = useState(30);
  const [scheduleSubmitting, setScheduleSubmitting] = useState(false);

  // Generate slots state
  const todayStr = new Date().toISOString().split('T')[0];
  const nextTwoWeeks = new Date();
  nextTwoWeeks.setDate(nextTwoWeeks.getDate() + 14);
  const nextTwoWeeksStr = nextTwoWeeks.toISOString().split('T')[0];

  const [genStartDate, setGenStartDate] = useState(todayStr);
  const [genEndDate, setGenEndDate] = useState(nextTwoWeeksStr);
  const [genLoading, setGenLoading] = useState(false);

  // Discrete slot creation
  const [customSlotDate, setCustomSlotDate] = useState(todayStr);
  const [customSlotStart, setCustomSlotStart] = useState('10:00');
  const [customSlotEnd, setCustomSlotEnd] = useState('10:30');
  const [customSlotLoading, setCustomSlotLoading] = useState(false);

  const loadDoctorData = async () => {
    if (!doctorId) return;
    setLoading(true);
    try {
      const [appts, scheds, doc] = await Promise.all([
        appointmentService.getMyAppointments(),
        doctorService.getDoctorSchedules(doctorId),
        doctorService.getDoctorById(doctorId)
      ]);
      setAppointments(appts);
      setSchedules(scheds);
      setDoctorProfile(doc);
    } catch (err) {
      console.error('Error loading doctor dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDoctorData();
  }, [doctorId]);

  const handleAddSchedule = async (e) => {
    e.preventDefault();
    setScheduleSubmitting(true);
    setStatusMsg({ type: '', text: '' });
    try {
      await doctorService.addDoctorSchedule(doctorId, {
        day_of_week: Number(dayOfWeek),
        start_time: startTime + ':00',
        end_time: endTime + ':00',
        slot_duration_minutes: Number(durationMinutes),
        is_active: true
      });
      setStatusMsg({ type: 'success', text: 'Recurring weekly schedule session added successfully.' });
      const updatedScheds = await doctorService.getDoctorSchedules(doctorId);
      setSchedules(updatedScheds);
    } catch (err) {
      setStatusMsg({ type: 'error', text: formatApiError(err, 'Failed to add schedule.') });
    } finally {
      setScheduleSubmitting(false);
    }
  };

  const handleGenerateSlots = async (e) => {
    e.preventDefault();
    setGenLoading(true);
    setStatusMsg({ type: '', text: '' });
    try {
      const generated = await availabilityService.generateSlots(doctorId, genStartDate, genEndDate);
      setStatusMsg({ type: 'success', text: `Generated ${generated.length} discrete consultation slots across the date window.` });
    } catch (err) {
      setStatusMsg({ type: 'error', text: formatApiError(err, 'Failed to generate availability slots.') });
    } finally {
      setGenLoading(false);
    }
  };

  const handleCreateCustomSlot = async (e) => {
    e.preventDefault();
    setCustomSlotLoading(true);
    setStatusMsg({ type: '', text: '' });
    try {
      await availabilityService.createSlot(doctorId, {
        slot_date: customSlotDate,
        start_time: customSlotStart + ':00',
        end_time: customSlotEnd + ':00',
        status: 'AVAILABLE'
      });
      setStatusMsg({ type: 'success', text: `Slot created successfully for ${customSlotDate} at ${customSlotStart}.` });
    } catch (err) {
      setStatusMsg({ type: 'error', text: formatApiError(err, 'Failed to create slot.') });
    } finally {
      setCustomSlotLoading(false);
    }
  };

  const daysMap = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

  const isVerified = doctorProfile?.is_verified ?? user?.is_verified;

  return (
    <div className="page-wrapper">
      <div className="container">
        {/* Verification Status Warning Banner */}
        {!isVerified && (
          <div style={{
            backgroundColor: 'var(--warning-bg)',
            border: '1px solid var(--warning-border)',
            borderRadius: 'var(--radius-lg)',
            padding: '1.25rem 1.5rem',
            marginBottom: '2rem',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '1rem'
          }}>
            <AlertCircle size={24} color="var(--warning)" style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <h4 style={{ color: 'var(--warning)', marginBottom: '0.25rem', fontSize: '1.05rem' }}>
                Medical License Verification Pending
              </h4>
              <p style={{ color: 'var(--text-body)', fontSize: '0.9rem', lineHeight: 1.5 }}>
                Your practitioner account is currently awaiting credential review by an administrator. In compliance with medical safety rules, patients cannot reserve consultations with your profile until your medical license is verified.
              </p>
            </div>
          </div>
        )}

        {/* Dashboard Title & Overview Header */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '2rem',
          flexWrap: 'wrap',
          gap: '1rem'
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.35rem' }}>
              <span className="badge badge-neutral">Healthcare Provider Portal</span>
              {isVerified ? (
                <span className="badge badge-success"><ShieldCheck size={12} /> Verified</span>
              ) : (
                <span className="badge badge-warning">Unverified</span>
              )}
            </div>
            <h2>Dr. {doctorProfile?.first_name || user?.first_name} {doctorProfile?.last_name || user?.last_name}</h2>
            <span style={{ color: 'var(--sage-500)', fontWeight: 600, fontSize: '0.95rem' }}>
              Specialty: {doctorProfile?.specialty || 'General'} &bull; License: {doctorProfile?.license_number}
            </span>
          </div>
        </div>

        {/* Status Alerts */}
        {statusMsg.text && (
          <div style={{
            backgroundColor: statusMsg.type === 'success' ? 'var(--success-bg)' : 'var(--danger-bg)',
            color: statusMsg.type === 'success' ? 'var(--success)' : 'var(--danger)',
            border: `1px solid ${statusMsg.type === 'success' ? 'var(--success-border)' : 'var(--danger-border)'}`,
            borderRadius: 'var(--radius-md)',
            padding: '1rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            marginBottom: '2rem'
          }}>
            {statusMsg.type === 'success' ? <CheckCircle2 size={20} /> : <AlertCircle size={20} />}
            <div style={{ flex: 1 }}>{String(statusMsg.text)}</div>
            <button onClick={() => setStatusMsg({ type: '', text: '' })} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'inherit' }}>&times;</button>
          </div>
        )}

        {/* Appointments Section */}
        <div style={{ marginBottom: '3rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <h3>Scheduled Consultations ({appointments.length})</h3>
          </div>

          {loading ? (
            <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
              <p style={{ color: 'var(--text-muted)' }}>Loading consultation appointments...</p>
            </div>
          ) : appointments.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', padding: '3rem 2rem' }}>
              <Calendar size={40} color="var(--sage-400)" style={{ margin: '0 auto 0.75rem auto' }} />
              <h4>No Patient Consultations Scheduled</h4>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                You have no active appointments booked yet. Once slots are generated and patients book, they will appear here.
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {appointments.map((appt) => (
                <div key={appt.id} className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.35rem' }}>
                      <span className="badge badge-success">{appt.status}</span>
                      <span style={{ fontSize: '0.8rem', fontFamily: 'monospace', color: 'var(--text-subtle)' }}>
                        {appt.appointment_reference}
                      </span>
                    </div>
                    <h4 style={{ fontSize: '1.15rem', color: 'var(--text-main)', marginBottom: '0.25rem' }}>
                      Patient: {appt.patient_name || 'Registered Patient'}
                    </h4>
                    <p style={{ fontSize: '0.88rem', color: 'var(--text-body)' }}>
                      <strong>Complaint:</strong> {appt.chief_complaint}
                    </p>
                  </div>

                  <div style={{ textAlign: 'right' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--primary-800)', fontWeight: 600 }}>
                      <Clock size={16} />
                      <span>{formatReadableDateTime(appt.appointment_datetime)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Schedule & Availability Management Section */}
        <h3 style={{ marginBottom: '1.25rem' }}>Schedule & Availability Management</h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
          {/* Card 1: Add Recurring Weekly Template */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <Settings size={20} color="var(--primary-700)" />
              <h4 style={{ fontSize: '1.1rem' }}>Add Recurring Weekly Hours</h4>
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
              Configure your standard working hours per weekday. Multiple sessions per day are supported (e.g. morning and afternoon).
            </p>

            <form onSubmit={handleAddSchedule}>
              <div className="form-group">
                <label className="form-label">Day of Week</label>
                <select
                  className="form-select"
                  value={dayOfWeek}
                  onChange={(e) => setDayOfWeek(e.target.value)}
                >
                  {daysMap.map((name, idx) => (
                    <option key={name} value={idx}>{name}</option>
                  ))}
                </select>
              </div>

              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Start Time</label>
                  <input
                    type="time"
                    className="form-input"
                    value={startTime}
                    onChange={(e) => setStartTime(e.target.value)}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">End Time</label>
                  <input
                    type="time"
                    className="form-input"
                    value={endTime}
                    onChange={(e) => setEndTime(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Slot Duration (Minutes)</label>
                <select
                  className="form-select"
                  value={durationMinutes}
                  onChange={(e) => setDurationMinutes(e.target.value)}
                >
                  <option value={15}>15 Minutes</option>
                  <option value={30}>30 Minutes</option>
                  <option value={45}>45 Minutes</option>
                  <option value={60}>60 Minutes</option>
                </select>
              </div>

              <button
                type="submit"
                className="btn btn-primary btn-sm"
                style={{ width: '100%', marginTop: '0.5rem' }}
                disabled={scheduleSubmitting}
              >
                {scheduleSubmitting ? 'Saving Session...' : 'Save Weekly Session'}
              </button>
            </form>
          </div>

          {/* Card 2: Generate Slots from Templates */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <CalendarPlus size={20} color="var(--primary-700)" />
              <h4 style={{ fontSize: '1.1rem' }}>Generate Calendar Slots</h4>
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
              Batch-create bookable calendar slots for an upcoming date range based on your active weekly schedule sessions.
            </p>

            <form onSubmit={handleGenerateSlots}>
              <div className="form-group">
                <label className="form-label">From Date</label>
                <input
                  type="date"
                  className="form-input"
                  value={genStartDate}
                  onChange={(e) => setGenStartDate(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">To Date</label>
                <input
                  type="date"
                  className="form-input"
                  value={genEndDate}
                  onChange={(e) => setGenEndDate(e.target.value)}
                  required
                />
              </div>

              <button
                type="submit"
                className="btn btn-secondary btn-sm"
                style={{ width: '100%', marginTop: '1.5rem' }}
                disabled={genLoading || schedules.length === 0}
              >
                {genLoading ? 'Generating Slots...' : 'Generate Open Slots'}
              </button>

              {schedules.length === 0 && (
                <span style={{ fontSize: '0.8rem', color: 'var(--warning)', display: 'block', marginTop: '0.5rem', textAlign: 'center' }}>
                  Please save at least one recurring weekly session first.
                </span>
              )}
            </form>
          </div>

          {/* Card 3: Create Individual Slot */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <Plus size={20} color="var(--primary-700)" />
              <h4 style={{ fontSize: '1.1rem' }}>Create Discrete Slot</h4>
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
              Manually add a single consultation slot for a specific date and time without modifying your recurring template.
            </p>

            <form onSubmit={handleCreateCustomSlot}>
              <div className="form-group">
                <label className="form-label">Date</label>
                <input
                  type="date"
                  className="form-input"
                  value={customSlotDate}
                  onChange={(e) => setCustomSlotDate(e.target.value)}
                  required
                />
              </div>

              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Start Time</label>
                  <input
                    type="time"
                    className="form-input"
                    value={customSlotStart}
                    onChange={(e) => setCustomSlotStart(e.target.value)}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">End Time</label>
                  <input
                    type="time"
                    className="form-input"
                    value={customSlotEnd}
                    onChange={(e) => setCustomSlotEnd(e.target.value)}
                    required
                  />
                </div>
              </div>

              <button
                type="submit"
                className="btn btn-outline btn-sm"
                style={{ width: '100%', marginTop: '1rem' }}
                disabled={customSlotLoading}
              >
                {customSlotLoading ? 'Creating Slot...' : 'Add Slot to Calendar'}
              </button>
            </form>
          </div>
        </div>

        {/* Existing Active Weekly Sessions Display */}
        <div style={{ marginTop: '2.5rem' }}>
          <h4 style={{ marginBottom: '1rem' }}>Configured Weekly Schedule Templates</h4>
          {schedules.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No weekly schedule sessions configured yet.</p>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '1rem' }}>
              {schedules.map((s) => (
                <div key={s.id} className="card" style={{ padding: '1rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                    <strong style={{ color: 'var(--primary-800)' }}>{daysMap[s.day_of_week]}</strong>
                    <span className="badge badge-neutral" style={{ fontSize: '0.65rem' }}>Active</span>
                  </div>
                  <div style={{ fontSize: '0.88rem', color: 'var(--text-body)' }}>
                    {format12HourRange(s.start_time, s.end_time)}
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                    Slot interval: {s.slot_duration_minutes} mins
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

