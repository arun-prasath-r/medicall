import React from 'react';
import { Link } from 'react-router-dom';
import { Home, ArrowLeft, Stethoscope } from 'lucide-react';

export const NotFoundPage = () => {
  return (
    <div style={{
      minHeight: '70vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 'var(--spacing-8) var(--spacing-4)',
      textAlign: 'center'
    }}>
      <div style={{ maxWidth: '500px' }}>
        <div style={{
          width: '80px',
          height: '80px',
          borderRadius: 'var(--radius-full)',
          backgroundColor: 'var(--primary-50)',
          color: 'var(--primary-700)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto var(--spacing-6)'
        }}>
          <Stethoscope size={40} />
        </div>
        
        <h1 style={{ fontSize: '3rem', fontWeight: 800, color: 'var(--primary-900)', marginBottom: 'var(--spacing-2)' }}>
          404
        </h1>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--text-dark)', marginBottom: 'var(--spacing-3)' }}>
          Page Not Found
        </h2>
        <p style={{ color: 'var(--text-light)', marginBottom: 'var(--spacing-6)', lineHeight: 1.6 }}>
          We couldn't find the page you were looking for. It might have been moved, deleted, or never existed in the clinic records.
        </p>

        <div style={{ display: 'flex', gap: 'var(--spacing-3)', justifyContent: 'center', flexWrap: 'wrap' }}>
          <button
            onClick={() => window.history.back()}
            className="btn btn-outline"
            style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-2)' }}
          >
            <ArrowLeft size={16} />
            Go Back
          </button>
          <Link
            to="/"
            className="btn btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-2)' }}
          >
            <Home size={16} />
            Return Home
          </Link>
        </div>
      </div>
    </div>
  );
};

