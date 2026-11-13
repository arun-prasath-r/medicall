import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { patientService } from '../services/patientService';
import { appointmentService } from '../services/appointmentService';
import { 
  Calendar, 
  Clock, 
  Stethoscope, 
  User, 
  ArrowRight, 
  Sparkles, 
  CheckCircle2, 
  AlertCircle,
  FileText
} from 'lucide-react';
import { formatReadableDateTime } from '../utils/dateTime';

export const PatientDashboardPage = () => {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPatientData = async () => {
      setLoading(true);
      try {
        const [profData, apptData] = await Promise.all([
          patientService.getProfile(),
          appointmentService.getMyAppointments()
        ]);
        setProfile(profData);
        setAppointments(apptData);
      } catch (err) {
        console.error('Error loading dashboard data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchPatientData();
  }, []);

  const upcomingAppointments = appointments.filter(
    (a) => a.status === 'SCHEDULED' || a.status === 'RESCHEDULED'
  );

  return (
    <div className="page-wrapper">
      <div className="container">
        {/* Welcome Header */}
        <div style={{
          backgroundColor: 'var(--primary-800)',
          color: 'white',
          borderRadius: 'var(--radius-xl)',
          padding: '2.5rem',
          marginBottom: '2.5rem',
          boxShadow: 'var(--shadow-md)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1.5rem'
        }}>
          <div>
            <span className="badge badge-neutral" style={{ backgroundColor: 'rgba(255, 255, 255, 0.15)', color: 'white', border: 'none', marginBottom: '0.75rem' }}>
              Patient Portal
            </span>
            <h1 style={{ color: 'white', fontSize: '2rem', marginBottom: '0.5rem' }}>
              Welcome back, {profile?.first_name || user?.first_name || 'Patient'}!
            </h1>
            <p style={{ color: 'var(--sage-200)', fontSize: '1rem', maxWidth: '580px' }}>
              Access your medical consultation schedule, discover board-certified healthcare providers, and manage your health records.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            <Link to="/assistant" className="btn btn-primary" style={{ backgroundColor: 'var(--primary-600)', borderColor: 'var(--primary-500)', color: 'white' }}>
              <Sparkles size={18} />
              <span>AI Assistant</span>
            </Link>
            <Link to="/doctors" className="btn btn-secondary" style={{ backgroundColor: 'white', color: 'var(--primary-900)' }}>
              <Stethoscope size={18} />
              <span>Book Doctor</span>
            </Link>
          </div>
        </div>

        {/* AI Health Assistant Active Banner */}
        <div style={{
          backgroundColor: 'var(--primary-50)',
          border: '1.5px solid var(--primary-200)',
          borderRadius: 'var(--radius-lg)',
          padding: '1.5rem 1.75rem',
          marginBottom: '2.5rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1.25rem',
          boxShadow: 'var(--shadow-sm)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
            <div style={{
              width: '48px',
              height: '48px',
              borderRadius: 'var(--radius-md)',
              background: 'linear-gradient(135deg, var(--primary-700), var(--primary-800))',
              color: 'white',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
              boxShadow: '0 4px 12px rgba(26, 61, 50, 0.2)'
            }}>
              <Sparkles size={24} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
                <span className="badge badge-success" style={{ fontSize: '0.72rem', padding: '0.2rem 0.5rem' }}>
                  Live Feature
                </span>
                <h4 style={{ fontSize: '1.15rem', color: 'var(--primary-900)', margin: 0, fontWeight: 700 }}>
                  AI Clinical Voice Assistant
                </h4>
              </div>
              <p style={{ fontSize: '0.92rem', color: 'var(--text-body)', margin: 0, maxWidth: '620px' }}>
                Experience hands-free clinical triage powered by Google Gemini. Speak naturally to find doctors, review availability, and schedule consultations with secure patient confirmation.
              </p>
            </div>
          </div>
          <Link to="/assistant" className="btn btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
            <span>Launch Assistant</span>
            <ArrowRight size={16} />
          </Link>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '2rem' }}>
          {/* Upcoming Consultations */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <h3>Upcoming Appointments</h3>
              <Link to="/appointments" style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--primary-700)' }}>
                View All ({appointments.length}) &rarr;
              </Link>
            </div>

            {loading ? (
              <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
                <p style={{ color: 'var(--text-muted)' }}>Loading appointments...</p>
              </div>
            ) : upcomingAppointments.length === 0 ? (
              <div className="card" style={{ textAlign: 'center', padding: '3rem 2rem' }}>
                <Calendar size={40} color="var(--sage-400)" style={{ margin: '0 auto 0.75rem auto' }} />
                <h4>No Upcoming Appointments</h4>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.25rem' }}>
                  You don't have any scheduled consultations at the moment.
                </p>
                <Link to="/doctors" className="btn btn-primary btn-sm">
                  Find a Doctor Now
                </Link>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {upcomingAppointments.map((appt) => (
                  <div key={appt.id} className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.35rem' }}>
                        <span className="badge badge-success">{appt.status}</span>
                        <span style={{ fontSize: '0.8rem', fontFamily: 'monospace', color: 'var(--text-subtle)' }}>
                          {appt.appointment_reference}
                        </span>
                      </div>
                      <h4 style={{ fontSize: '1.1rem', color: 'var(--text-main)', marginBottom: '0.2rem' }}>
                        {appt.doctor_name || 'Assigned Practitioner'}
                      </h4>
                      <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'block' }}>
                        Specialty: {appt.doctor_specialty || 'General Care'}
                      </span>
                    </div>

                    <div style={{ textAlign: 'right' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--primary-700)', fontWeight: 600, fontSize: '0.92rem' }}>
                        <Clock size={16} />
                        <span>{formatReadableDateTime(appt.appointment_datetime)}</span>
                      </div>
                      <Link to="/appointments" className="btn btn-outline btn-sm" style={{ marginTop: '0.5rem' }}>
                        Manage
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Patient Health Profile Card */}
          <div>
            <h3 style={{ marginBottom: '1.25rem' }}>My Health Profile</h3>
            <div className="card">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem', marginBottom: '1.25rem', paddingBottom: '1rem', borderBottom: '1px solid var(--border-light)' }}>
                <div style={{
                  width: '44px',
                  height: '44px',
                  borderRadius: '50%',
                  backgroundColor: 'var(--primary-100)',
                  color: 'var(--primary-700)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 700
                }}>
                  {profile?.first_name?.[0] || 'P'}
                </div>
                <div>
                  <h4 style={{ fontSize: '1.05rem', marginBottom: '0.1rem' }}>
                    {profile?.first_name} {profile?.last_name}
                  </h4>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{user?.email}</span>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', fontSize: '0.88rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Date of Birth:</span>
                  <strong>{profile?.date_of_birth || 'Not specified'}</strong>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Blood Group:</span>
                  <span className="badge badge-neutral">{profile?.blood_group || 'Unknown'}</span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Gender:</span>
                  <strong>{profile?.gender || 'Not specified'}</strong>
                </div>

                <div>
                  <span style={{ color: 'var(--text-muted)', display: 'block', marginBottom: '0.2rem' }}>Allergies:</span>
                  <span style={{ color: 'var(--text-body)' }}>{profile?.allergies || 'None documented'}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

