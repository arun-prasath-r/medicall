import React from 'react';
import { Link } from 'react-router-dom';
import { 
  Stethoscope, 
  CalendarCheck, 
  ShieldCheck, 
  Clock, 
  ArrowRight, 
  HeartHandshake, 
  Search, 
  CheckCircle2, 
  Activity,
  Sparkles
} from 'lucide-react';

export const LandingPage = () => {
  return (
    <div>
      {/* Hero Section */}
      <section style={{
        background: 'linear-gradient(180deg, #f0f6f3 0%, #fbfbf9 100%)',
        paddingTop: '4.5rem',
        paddingBottom: '5rem',
        borderBottom: '1px solid var(--border-light)'
      }}>
        <div className="container" style={{ textAlign: 'center', maxWidth: '880px' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.4rem 1rem',
            backgroundColor: 'var(--sage-100)',
            border: '1px solid var(--sage-200)',
            borderRadius: 'var(--radius-full)',
            color: 'var(--primary-800)',
            fontSize: '0.85rem',
            fontWeight: 600,
            marginBottom: '1.75rem'
          }}>
            <Sparkles size={16} color="var(--primary-600)" />
            <span>Digital Healthcare SaaS &bull; Verified Doctor Consultations</span>
          </div>

          <h1 style={{
            fontSize: 'clamp(2.4rem, 5vw, 3.8rem)',
            color: 'var(--primary-900)',
            lineHeight: 1.15,
            marginBottom: '1.5rem',
            fontWeight: 800
          }}>
            Intelligent healthcare scheduling, designed for care.
          </h1>

          <p style={{
            fontSize: '1.18rem',
            color: 'var(--text-body)',
            lineHeight: 1.6,
            marginBottom: '2.5rem',
            maxWidth: '680px',
            marginLeft: 'auto',
            marginRight: 'auto'
          }}>
            Medicall connects patients with board-certified healthcare providers through real-time calendar slot availability, conflict-free booking, and clinical safety guardrails.
          </p>

          <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
            <Link to="/doctors" className="btn btn-primary btn-lg" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Search size={18} />
              <span>Find a Doctor</span>
            </Link>
            <Link to="/register" className="btn btn-outline btn-lg" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span>Get Started</span>
              <ArrowRight size={18} />
            </Link>
          </div>

          {/* Trust Highlights */}
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            gap: '2.5rem',
            marginTop: '3.5rem',
            flexWrap: 'wrap',
            color: 'var(--text-muted)',
            fontSize: '0.9rem'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <CheckCircle2 size={18} color="var(--primary-600)" />
              <span>Board-Certified Specialists</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <ShieldCheck size={18} color="var(--primary-600)" />
              <span>PostgreSQL Concurrency Locking</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Activity size={18} color="var(--primary-600)" />
              <span>Zero Double-Booking Guarantee</span>
            </div>
          </div>
        </div>
      </section>

      {/* How it Works Section */}
      <section style={{ padding: '5rem 0', backgroundColor: 'var(--bg-surface)' }}>
        <div className="container">
          <div style={{ textAlign: 'center', maxWidth: '640px', margin: '0 auto 3.5rem auto' }}>
            <span className="badge badge-neutral" style={{ marginBottom: '0.75rem' }}>Simple 3-Step Process</span>
            <h2>How Medicall Simplifies Your Care</h2>
            <p style={{ color: 'var(--text-muted)', marginTop: '0.5rem' }}>
              From discovering the right medical specialty to securing your consultation time without phone queues.
            </p>
          </div>

          <div className="grid-3">
            <div className="card" style={{ padding: '2rem' }}>
              <div style={{
                width: '48px',
                height: '48px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--primary-50)',
                color: 'var(--primary-700)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '1.25rem'
              }}>
                <Stethoscope size={24} />
              </div>
              <h3 style={{ fontSize: '1.2rem', marginBottom: '0.65rem' }}>1. Discover Specialists</h3>
              <p style={{ fontSize: '0.92rem', color: 'var(--text-body)', lineHeight: 1.6 }}>
                Browse verified medical professionals by specialty, experience, and consultation fees with transparent credentials.
              </p>
            </div>

            <div className="card" style={{ padding: '2rem' }}>
              <div style={{
                width: '48px',
                height: '48px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--primary-50)',
                color: 'var(--primary-700)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '1.25rem'
              }}>
                <Clock size={24} />
              </div>
              <h3 style={{ fontSize: '1.2rem', marginBottom: '0.65rem' }}>2. Pick Available Slots</h3>
              <p style={{ fontSize: '0.92rem', color: 'var(--text-body)', lineHeight: 1.6 }}>
                Inspect live calendar slots generated directly from doctor schedules. What you see is available in real time.
              </p>
            </div>

            <div className="card" style={{ padding: '2rem' }}>
              <div style={{
                width: '48px',
                height: '48px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--primary-50)',
                color: 'var(--primary-700)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '1.25rem'
              }}>
                <CalendarCheck size={24} />
              </div>
              <h3 style={{ fontSize: '1.2rem', marginBottom: '0.65rem' }}>3. Instant Confirmation</h3>
              <p style={{ fontSize: '0.92rem', color: 'var(--text-body)', lineHeight: 1.6 }}>
                Confirm your appointment with a unique booking reference ID. Manage, reschedule, or cancel anytime with one click.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Specialty Highlights */}
      <section style={{ padding: '4.5rem 0', backgroundColor: 'var(--bg-app)', borderTop: '1px solid var(--border-light)' }}>
        <div className="container">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '2.5rem', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <span className="badge badge-neutral" style={{ marginBottom: '0.5rem' }}>Specialty Directory</span>
              <h2>Comprehensive Medical Disciplines</h2>
            </div>
            <Link to="/doctors" className="btn btn-outline btn-sm">
              View All Doctors &rarr;
            </Link>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem' }}>
            {['Cardiology', 'Dermatology', 'Family Medicine', 'Neurology', 'Pediatrics', 'Immunology'].map((spec) => (
              <Link 
                key={spec} 
                to={`/doctors?specialty=${encodeURIComponent(spec)}`}
                className="card card-hover"
                style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.75rem', textDecoration: 'none' }}
              >
                <div style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '50%',
                  backgroundColor: 'var(--sage-100)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--primary-700)'
                }}>
                  <Activity size={18} />
                </div>
                <div>
                  <h4 style={{ fontSize: '0.95rem', color: 'var(--text-main)', marginBottom: '0.1rem' }}>{spec}</h4>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Browse Doctors</span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Practitioner CTA */}
      <section style={{
        padding: '4rem 0',
        backgroundColor: 'var(--primary-800)',
        color: 'white',
        borderTop: '1px solid var(--primary-700)'
      }}>
        <div className="container" style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '2rem'
        }}>
          <div style={{ maxWidth: '600px' }}>
            <h2 style={{ color: 'white', marginBottom: '0.75rem' }}>Are you a licensed healthcare provider?</h2>
            <p style={{ color: 'var(--sage-200)', fontSize: '1.05rem', lineHeight: 1.6 }}>
              Join the Medicall clinical network. Configure your weekly consulting hours, manage appointments, and streamline patient intake.
            </p>
          </div>
          <Link to="/register?role=DOCTOR" className="btn btn-secondary btn-lg" style={{ backgroundColor: 'white', color: 'var(--primary-900)' }}>
            <HeartHandshake size={20} />
            <span>Register as Doctor</span>
          </Link>
        </div>
      </section>
    </div>
  );
};

