import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { 
  HeartPulse, 
  Calendar, 
  User, 
  LogOut, 
  ShieldCheck, 
  Menu, 
  X, 
  Stethoscope,
  LayoutDashboard,
  Sparkles
} from 'lucide-react';

export const Navbar = () => {
  const { user, isAuthenticated, isPatient, isDoctor, isAdmin, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const isActive = (path) => location.pathname === path;

  return (
    <header style={{
      backgroundColor: 'var(--bg-surface)',
      borderBottom: '1px solid var(--border-light)',
      position: 'sticky',
      top: 0,
      zIndex: 50,
      boxShadow: 'var(--shadow-xs)'
    }}>
      <div className="container" style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        height: '72px'
      }}>
        {/* Brand Logo */}
        <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', textDecoration: 'none' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--primary-700)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white'
          }}>
            <HeartPulse size={24} />
          </div>
          <div>
            <span style={{
              fontFamily: 'var(--font-display)',
              fontSize: '1.45rem',
              fontWeight: 700,
              color: 'var(--primary-800)',
              letterSpacing: '-0.02em',
              display: 'block',
              lineHeight: 1.1
            }}>
              Medicall
            </span>
            <span style={{
              fontSize: '0.7rem',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              fontWeight: 600,
              color: 'var(--sage-500)',
              display: 'block'
            }}>
              Healthcare SaaS
            </span>
          </div>
        </Link>

        {/* Desktop Navigation Links */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '1.75rem' }} className="desktop-nav">
          <Link 
            to="/doctors" 
            style={{ 
              fontWeight: 500, 
              color: isActive('/doctors') ? 'var(--primary-700)' : 'var(--text-body)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem'
            }}
          >
            <Stethoscope size={18} />
            Find Doctors
          </Link>

          {isAuthenticated && isPatient && (
            <>
              <Link 
                to="/dashboard" 
                style={{ 
                  fontWeight: 500, 
                  color: isActive('/dashboard') ? 'var(--primary-700)' : 'var(--text-body)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.35rem'
                }}
              >
                <LayoutDashboard size={18} />
                Dashboard
              </Link>
              <Link 
                to="/appointments" 
                style={{ 
                  fontWeight: 500, 
                  color: isActive('/appointments') ? 'var(--primary-700)' : 'var(--text-body)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.35rem'
                }}
              >
                <Calendar size={18} />
                My Appointments
              </Link>
              <Link 
                to="/assistant" 
                style={{ 
                  fontWeight: 600, 
                  color: isActive('/assistant') ? 'var(--primary-700)' : 'var(--primary-600)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                  backgroundColor: isActive('/assistant') ? 'var(--primary-50)' : 'transparent',
                  padding: '0.4rem 0.75rem',
                  borderRadius: 'var(--radius-full)',
                  border: isActive('/assistant') ? '1px solid var(--primary-200)' : '1px solid transparent',
                  transition: 'all var(--transition-fast)'
                }}
              >
                <Sparkles size={17} color="var(--primary-600)" />
                AI Assistant
              </Link>
            </>
          )}

          {isAuthenticated && isDoctor && (
            <Link 
              to="/doctor/dashboard" 
              style={{ 
                fontWeight: 500, 
                color: isActive('/doctor/dashboard') ? 'var(--primary-700)' : 'var(--text-body)',
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem'
              }}
            >
              <LayoutDashboard size={18} />
              Doctor Portal
            </Link>
          )}

          {isAuthenticated && isAdmin && (
            <Link 
              to="/admin" 
              style={{ 
                fontWeight: 600, 
                color: isActive('/admin') ? 'var(--primary-700)' : 'var(--text-body)',
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem'
              }}
            >
              <ShieldCheck size={18} color="var(--primary-600)" />
              Admin Verification
            </Link>
          )}
        </nav>

        {/* Action Buttons / User Menu */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          {isAuthenticated ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.35rem 0.85rem',
                backgroundColor: 'var(--sage-50)',
                border: '1px solid var(--border-light)',
                borderRadius: 'var(--radius-full)'
              }}>
                <User size={16} color="var(--primary-700)" />
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--primary-800)' }}>
                  {user.first_name || user.email.split('@')[0]}
                </span>
                <span className="badge badge-neutral" style={{ fontSize: '0.65rem', padding: '0.1rem 0.4rem' }}>
                  {user.role}
                </span>
              </div>
              <button 
                onClick={handleLogout} 
                className="btn btn-outline btn-sm"
                title="Log Out"
                style={{ padding: '0.45rem' }}
              >
                <LogOut size={16} />
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <Link to="/login" className="btn btn-outline btn-sm">
                Sign In
              </Link>
              <Link to="/register" className="btn btn-primary btn-sm">
                Get Started
              </Link>
            </div>
          )}

          {/* Mobile menu toggle */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            style={{
              display: 'none',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--text-main)'
            }}
            className="mobile-toggle"
          >
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div style={{
          backgroundColor: 'var(--bg-surface)',
          borderBottom: '1px solid var(--border-light)',
          padding: '1rem 1.5rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem'
        }}>
          <Link to="/doctors" onClick={() => setMobileMenuOpen(false)}>Find Doctors</Link>
          {isAuthenticated && isPatient && (
            <>
              <Link to="/dashboard" onClick={() => setMobileMenuOpen(false)}>Patient Dashboard</Link>
              <Link to="/appointments" onClick={() => setMobileMenuOpen(false)}>My Appointments</Link>
              <Link to="/assistant" onClick={() => setMobileMenuOpen(false)} style={{ fontWeight: 600, color: 'var(--primary-700)' }}>
                ✨ AI Voice Assistant
              </Link>
            </>
          )}
          {isAuthenticated && isDoctor && (
            <Link to="/doctor/dashboard" onClick={() => setMobileMenuOpen(false)}>Doctor Portal</Link>
          )}
          {isAuthenticated && isAdmin && (
            <Link to="/admin" onClick={() => setMobileMenuOpen(false)}>Admin Verification</Link>
          )}
        </div>
      )}
    </header>
  );
};

