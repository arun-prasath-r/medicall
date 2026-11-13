import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { 
  HeartPulse, 
  User, 
  Stethoscope, 
  ArrowRight, 
  AlertCircle, 
  CheckCircle2, 
  Clock 
} from 'lucide-react';
import { formatApiError } from '../utils/errorUtils';

export const RegisterPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { register } = useAuth();

  const [role, setRole] = useState('PATIENT');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successData, setSuccessData] = useState(null);

  // Common Form Fields
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');

  // Patient Fields
  const [dateOfBirth, setDateOfBirth] = useState('');
  const [gender, setGender] = useState('Male');
  const [bloodGroup, setBloodGroup] = useState('O+');
  const [allergies, setAllergies] = useState('');

  // Doctor Fields
  const [licenseNumber, setLicenseNumber] = useState('');
  const [specialty, setSpecialty] = useState('General Medicine');
  const [qualifications, setQualifications] = useState('');
  const [experienceYears, setExperienceYears] = useState(5);
  const [consultationFee, setConsultationFee] = useState(100);
  const [clinicAddress, setClinicAddress] = useState('');
  const [bio, setBio] = useState('');

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const roleParam = params.get('role');
    if (roleParam === 'DOCTOR') setRole('DOCTOR');
  }, [location]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const payload = {
      email,
      password,
      role,
      first_name: firstName,
      last_name: lastName,
      phone_number: phoneNumber || undefined,
    };

    if (role === 'PATIENT') {
      payload.date_of_birth = dateOfBirth;
      payload.gender = gender;
      payload.blood_group = bloodGroup;
      payload.allergies = allergies || undefined;
    } else {
      payload.license_number = licenseNumber;
      payload.specialty = specialty;
      payload.qualifications = qualifications;
      payload.experience_years = Number(experienceYears);
      payload.consultation_fee = Number(consultationFee);
      payload.clinic_address = clinicAddress || undefined;
      payload.bio = bio || undefined;
    }

    try {
      const resp = await register(payload);
      setSuccessData(resp);
    } catch (err) {
      console.error('Registration error:', err);
      const msg = formatApiError(err, 'Registration failed. Please check the provided information.');
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  if (successData) {
    return (
      <div className="page-wrapper" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div className="container container-narrow">
          <div className="card" style={{ maxWidth: '520px', margin: '0 auto', textAlign: 'center', padding: '3rem 2rem' }}>
            <div style={{
              width: '56px',
              height: '56px',
              borderRadius: '50%',
              backgroundColor: 'var(--success-bg)',
              color: 'var(--success)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 1.25rem auto'
            }}>
              <CheckCircle2 size={32} />
            </div>

            <h2 style={{ fontSize: '1.75rem', marginBottom: '0.75rem' }}>Registration Successful!</h2>
            
            {role === 'DOCTOR' ? (
              <div style={{
                backgroundColor: 'var(--warning-bg)',
                border: '1px solid var(--warning-border)',
                borderRadius: 'var(--radius-md)',
                padding: '1rem',
                margin: '1.5rem 0',
                textAlign: 'left'
              }}>
                <div style={{ display: 'flex', gap: '0.5rem', color: 'var(--warning)', fontWeight: 600, marginBottom: '0.25rem' }}>
                  <Clock size={18} />
                  <span>Credential Verification Pending</span>
                </div>
                <p style={{ fontSize: '0.88rem', color: 'var(--text-body)', lineHeight: 1.5 }}>
                  Your doctor profile has been created. In accordance with clinical safety regulations, your account must be verified by an administrator before your availability can be booked by patients.
                </p>
              </div>
            ) : (
              <p style={{ color: 'var(--text-muted)', marginBottom: '2rem', fontSize: '0.95rem' }}>
                Your patient account has been created and verified. You can now sign in to discover doctors and manage consultations.
              </p>
            )}

            <Link to="/login" className="btn btn-primary btn-lg" style={{ width: '100%' }}>
              Proceed to Sign In
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page-wrapper">
      <div className="container container-narrow">
        <div className="card" style={{ maxWidth: '640px', margin: '0 auto', padding: '2.5rem' }}>
          {/* Header */}
          <div style={{ textAlign: 'center', marginBottom: '1.75rem' }}>
            <h2 style={{ fontSize: '1.75rem', marginBottom: '0.35rem' }}>Create Your Account</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.92rem' }}>
              Select your role to get started with Medicall
            </p>
          </div>

          {/* Role Toggle Tabs */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '0.5rem',
            padding: '0.35rem',
            backgroundColor: 'var(--bg-subtle)',
            borderRadius: 'var(--radius-md)',
            marginBottom: '2rem'
          }}>
            <button
              type="button"
              onClick={() => { setRole('PATIENT'); setError(''); }}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem',
                padding: '0.75rem',
                borderRadius: 'var(--radius-sm)',
                border: 'none',
                fontWeight: 600,
                fontSize: '0.9rem',
                cursor: 'pointer',
                backgroundColor: role === 'PATIENT' ? 'var(--bg-surface)' : 'transparent',
                color: role === 'PATIENT' ? 'var(--primary-800)' : 'var(--text-muted)',
                boxShadow: role === 'PATIENT' ? 'var(--shadow-xs)' : 'none',
                transition: 'all var(--transition-fast)'
              }}
            >
              <User size={18} />
              <span>I am a Patient</span>
            </button>

            <button
              type="button"
              onClick={() => { setRole('DOCTOR'); setError(''); }}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem',
                padding: '0.75rem',
                borderRadius: 'var(--radius-sm)',
                border: 'none',
                fontWeight: 600,
                fontSize: '0.9rem',
                cursor: 'pointer',
                backgroundColor: role === 'DOCTOR' ? 'var(--bg-surface)' : 'transparent',
                color: role === 'DOCTOR' ? 'var(--primary-800)' : 'var(--text-muted)',
                boxShadow: role === 'DOCTOR' ? 'var(--shadow-xs)' : 'none',
                transition: 'all var(--transition-fast)'
              }}
            >
              <Stethoscope size={18} />
              <span>I am a Doctor</span>
            </button>
          </div>

          {error && (
            <div style={{
              backgroundColor: 'var(--danger-bg)',
              color: 'var(--danger)',
              border: '1px solid var(--danger-border)',
              borderRadius: 'var(--radius-md)',
              padding: '0.75rem 1rem',
              fontSize: '0.88rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              marginBottom: '1.5rem'
            }}>
              <AlertCircle size={18} />
              <span>{String(error)}</span>
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="grid-2">
              <div className="form-group">
                <label className="form-label">First Name *</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Eleanor"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Last Name *</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Vance"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="grid-2">
              <div className="form-group">
                <label className="form-label">Email Address *</label>
                <input
                  type="email"
                  className="form-input"
                  placeholder="name@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Phone Number</label>
                <input
                  type="tel"
                  className="form-input"
                  placeholder="+1-555-0100"
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Password * (Minimum 8 characters)</label>
              <input
                type="password"
                className="form-input"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                minLength={8}
                required
              />
            </div>

            {/* Role-Specific Fields */}
            {role === 'PATIENT' ? (
              <>
                <div className="grid-2">
                  <div className="form-group">
                    <label className="form-label">Date of Birth *</label>
                    <input
                      type="date"
                      className="form-input"
                      value={dateOfBirth}
                      onChange={(e) => setDateOfBirth(e.target.value)}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Gender</label>
                    <select
                      className="form-select"
                      value={gender}
                      onChange={(e) => setGender(e.target.value)}
                    >
                      <option value="Male">Male</option>
                      <option value="Female">Female</option>
                      <option value="Other">Other / Non-binary</option>
                      <option value="Prefer not to say">Prefer not to say</option>
                    </select>
                  </div>
                </div>

                <div className="grid-2">
                  <div className="form-group">
                    <label className="form-label">Blood Group</label>
                    <select
                      className="form-select"
                      value={bloodGroup}
                      onChange={(e) => setBloodGroup(e.target.value)}
                    >
                      {['O+', 'O-', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-'].map(bg => (
                        <option key={bg} value={bg}>{bg}</option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Known Allergies</label>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="e.g. Penicillin, Peanuts (optional)"
                      value={allergies}
                      onChange={(e) => setAllergies(e.target.value)}
                    />
                  </div>
                </div>
              </>
            ) : (
              <>
                <div className="grid-2">
                  <div className="form-group">
                    <label className="form-label">Medical License Number *</label>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="e.g. MD-LIC-98745"
                      value={licenseNumber}
                      onChange={(e) => setLicenseNumber(e.target.value)}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Specialty *</label>
                    <select
                      className="form-select"
                      value={specialty}
                      onChange={(e) => setSpecialty(e.target.value)}
                      required
                    >
                      <option value="General Medicine">General Medicine</option>
                      <option value="Cardiology">Cardiology</option>
                      <option value="Dermatology">Dermatology</option>
                      <option value="Neurology">Neurology</option>
                      <option value="Pediatrics">Pediatrics</option>
                      <option value="Immunology">Immunology</option>
                      <option value="Orthopedics">Orthopedics</option>
                      <option value="Psychiatry">Psychiatry</option>
                    </select>
                  </div>
                </div>

                <div className="grid-2">
                  <div className="form-group">
                    <label className="form-label">Qualifications *</label>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="e.g. MBBS, MD, FACC"
                      value={qualifications}
                      onChange={(e) => setQualifications(e.target.value)}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Experience (Years) *</label>
                    <input
                      type="number"
                      className="form-input"
                      min={0}
                      value={experienceYears}
                      onChange={(e) => setExperienceYears(e.target.value)}
                      required
                    />
                  </div>
                </div>

                <div className="grid-2">
                  <div className="form-group">
                    <label className="form-label">Consultation Fee ($ USD) *</label>
                    <input
                      type="number"
                      className="form-input"
                      min={0}
                      step="5"
                      value={consultationFee}
                      onChange={(e) => setConsultationFee(e.target.value)}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Clinic Location / Address</label>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="e.g. Suite 400, St. Jude Clinic"
                      value={clinicAddress}
                      onChange={(e) => setClinicAddress(e.target.value)}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">Professional Bio</label>
                  <textarea
                    className="form-textarea"
                    rows={2}
                    placeholder="Brief background on your clinical focus..."
                    value={bio}
                    onChange={(e) => setBio(e.target.value)}
                  />
                </div>
              </>
            )}

            <button
              type="submit"
              className="btn btn-primary btn-lg"
              style={{ width: '100%', marginTop: '1rem' }}
              disabled={loading}
            >
              {loading ? 'Creating Account...' : `Register as ${role === 'PATIENT' ? 'Patient' : 'Doctor'}`}
            </button>
          </form>

          <div style={{ textAlign: 'center', marginTop: '1.75rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
            Already have an account?{' '}
            <Link to="/login" style={{ fontWeight: 600, color: 'var(--primary-700)' }}>
              Sign In
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

