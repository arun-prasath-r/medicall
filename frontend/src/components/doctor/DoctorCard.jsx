import React from 'react';
import { Link } from 'react-router-dom';
import { Stethoscope, Award, MapPin, DollarSign, Calendar, ShieldCheck, AlertCircle } from 'lucide-react';

export const DoctorCard = ({ doctor }) => {
  return (
    <div className="card card-hover" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
        <div style={{ display: 'flex', gap: '0.85rem', alignItems: 'center' }}>
          <div style={{
            width: '52px',
            height: '52px',
            borderRadius: 'var(--radius-lg)',
            backgroundColor: 'var(--primary-100)',
            color: 'var(--primary-700)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.25rem',
            fontWeight: 700
          }}>
            {(doctor.first_name?.[0] || 'D')}{(doctor.last_name?.[0] || 'R')}
          </div>
          <div>
            <h3 style={{ fontSize: '1.15rem', color: 'var(--primary-900)', marginBottom: '0.15rem' }}>
              Dr. {doctor.first_name} {doctor.last_name}
            </h3>
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--sage-500)', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <Stethoscope size={14} />
              {doctor.specialty}
            </span>
          </div>
        </div>

        {doctor.is_verified ? (
          <span className="badge badge-success" title="Verified License Credentials">
            <ShieldCheck size={12} />
            Verified
          </span>
        ) : (
          <span className="badge badge-warning" title="Pending Verification">
            <AlertCircle size={12} />
            Pending
          </span>
        )}
      </div>

      {/* Qualifications & Experience */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem', fontSize: '0.88rem', color: 'var(--text-body)', marginBottom: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Award size={15} color="var(--text-subtle)" />
          <span>{doctor.qualifications} &bull; {doctor.experience_years} yrs exp</span>
        </div>
        {doctor.clinic_address && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <MapPin size={15} color="var(--text-subtle)" />
            <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{doctor.clinic_address}</span>
          </div>
        )}
      </div>

      {doctor.bio && (
        <p style={{
          fontSize: '0.85rem',
          color: 'var(--text-muted)',
          lineHeight: 1.5,
          marginBottom: '1.25rem',
          display: '-webkit-box',
          WebkitLineClamp: 2,
          WebkitBoxOrient: 'vertical',
          overflow: 'hidden'
        }}>
          {doctor.bio}
        </p>
      )}

      {/* Footer & Booking Action */}
      <div style={{
        marginTop: 'auto',
        paddingTop: '1rem',
        borderTop: '1px solid var(--border-light)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-subtle)', display: 'block' }}>Consultation Fee</span>
          <span style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--primary-800)' }}>
            ${Number(doctor.consultation_fee).toFixed(0)}
          </span>
        </div>

        <Link 
          to={`/doctors/${doctor.id}`} 
          className="btn btn-primary btn-sm"
          style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
        >
          <Calendar size={15} />
          <span>Book Slot</span>
        </Link>
      </div>
    </div>
  );
};
