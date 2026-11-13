import React from 'react';
import { HeartPulse, Shield, Clock, PhoneCall } from 'lucide-react';
import { Link } from 'react-router-dom';

export const Footer = () => {
  return (
    <footer style={{
      backgroundColor: 'var(--primary-900)',
      color: 'var(--sage-200)',
      paddingTop: '3.5rem',
      paddingBottom: '2rem',
      marginTop: 'auto',
      borderTop: '1px solid rgba(255, 255, 255, 0.08)'
    }}>
      <div className="container">
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '2.5rem',
          marginBottom: '3rem'
        }}>
          {/* Brand Info */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '1rem' }}>
              <div style={{
                width: '36px',
                height: '36px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--primary-600)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white'
              }}>
                <HeartPulse size={20} />
              </div>
              <span style={{
                fontFamily: 'var(--font-display)',
                fontSize: '1.35rem',
                fontWeight: 700,
                color: '#ffffff'
              }}>
                Medicall
              </span>
            </div>
            <p style={{ fontSize: '0.9rem', color: 'var(--sage-300)', lineHeight: 1.6, marginBottom: '1.25rem' }}>
              Intelligent healthcare scheduling and doctor consultation platform designed for accessibility and clinical safety.
            </p>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#fde68a', fontSize: '0.85rem' }}>
              <PhoneCall size={16} />
              <span>Emergency Services: <strong>911</strong> / <strong>112</strong></span>
            </div>
          </div>

          {/* Quick Navigation */}
          <div>
            <h4 style={{ color: '#ffffff', marginBottom: '1rem', fontSize: '1rem' }}>Platform</h4>
            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
              <li><Link to="/doctors" style={{ color: 'var(--sage-200)' }}>Find Registered Doctors</Link></li>
              <li><Link to="/register" style={{ color: 'var(--sage-200)' }}>Join as Patient</Link></li>
              <li><Link to="/register?role=DOCTOR" style={{ color: 'var(--sage-200)' }}>Join as Healthcare Provider</Link></li>
              <li><Link to="/login" style={{ color: 'var(--sage-200)' }}>Portal Sign In</Link></li>
            </ul>
          </div>

          {/* Clinical Safety & Guardrails */}
          <div>
            <h4 style={{ color: '#ffffff', marginBottom: '1rem', fontSize: '1rem' }}>Clinical Safety</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.88rem' }}>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}>
                <Shield size={16} color="var(--primary-300)" style={{ flexShrink: 0, marginTop: '3px' }} />
                <span>Deterministic red-flag triage filters prior to any AI interactions.</span>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}>
                <Clock size={16} color="var(--primary-300)" style={{ flexShrink: 0, marginTop: '3px' }} />
                <span>Real-time slot reservation backed by PostgreSQL concurrency locking.</span>
              </div>
            </div>
          </div>
        </div>

        {/* Medical Scope Disclaimer Banner */}
        <div style={{
          backgroundColor: 'rgba(255, 255, 255, 0.05)',
          borderRadius: 'var(--radius-md)',
          padding: '1rem 1.25rem',
          fontSize: '0.82rem',
          color: 'var(--sage-300)',
          lineHeight: 1.5,
          border: '1px solid rgba(255, 255, 255, 0.08)',
          marginBottom: '2rem'
        }}>
          <strong style={{ color: '#ffffff' }}>Medical Disclaimer:</strong> Medicall is an informational clinical assistance and appointment coordination tool. It is not a licensed medical practitioner and does not provide diagnostic decisions or emergency care. For life-threatening symptoms, immediately contact emergency services or proceed to the nearest emergency department.
        </div>

        {/* Copyright */}
        <div style={{
          borderTop: '1px solid rgba(255, 255, 255, 0.08)',
          paddingTop: '1.5rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          fontSize: '0.85rem'
        }}>
          <span>&copy; {new Date().getFullYear()} Medicall Systems Inc. All rights reserved.</span>
          <span style={{ color: 'var(--sage-400)' }}>Phase 2 Production Build &bull; React + FastAPI</span>
        </div>
      </div>
    </footer>
  );
};

