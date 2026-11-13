import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { doctorService } from '../services/doctorService';
import { DoctorCard } from '../components/doctor/DoctorCard';
import { Search, Filter, Stethoscope, RefreshCw, AlertCircle } from 'lucide-react';
import { formatApiError } from '../utils/errorUtils';

export const DoctorDirectoryPage = () => {
  const location = useLocation();
  const [doctors, setDoctors] = useState([]);
  const [specialties, setSpecialties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Filters
  const [selectedSpecialty, setSelectedSpecialty] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [maxFee, setMaxFee] = useState('');

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const specParam = params.get('specialty');
    if (specParam) setSelectedSpecialty(specParam);
  }, [location]);

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      const [docList, specList] = await Promise.all([
        doctorService.getDoctors({
          specialty: selectedSpecialty || undefined,
          max_fee: maxFee ? Number(maxFee) : undefined,
        }),
        doctorService.getSpecialties()
      ]);
      setDoctors(docList);
      setSpecialties(specList);
    } catch (err) {
      console.error('Error fetching doctors:', err);
      setError(formatApiError(err, 'Unable to load doctors. Please verify that the backend API is running.'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedSpecialty, maxFee]);

  // Client-side text filter for doctor name/qualifications
  const filteredDoctors = doctors.filter((doc) => {
    const fullName = `${doc.first_name} ${doc.last_name}`.toLowerCase();
    const query = searchQuery.toLowerCase();
    return fullName.includes(query) || doc.specialty.toLowerCase().includes(query) || doc.qualifications.toLowerCase().includes(query);
  });

  return (
    <div className="page-wrapper">
      <div className="container">
        {/* Header Banner */}
        <div style={{ marginBottom: '2.5rem' }}>
          <span className="badge badge-neutral" style={{ marginBottom: '0.5rem' }}>Clinical Specialists</span>
          <h2>Doctor Directory</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '1rem', marginTop: '0.25rem' }}>
            Discover licensed healthcare providers and book real-time consultation slots.
          </p>
        </div>

        {/* Filter & Search Bar */}
        <div className="card" style={{ padding: '1.25rem', marginBottom: '2.5rem' }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '1rem',
            alignItems: 'center'
          }}>
            {/* Search Input */}
            <div style={{ position: 'relative' }}>
              <input
                type="text"
                className="form-input"
                style={{ paddingLeft: '2.25rem' }}
                placeholder="Search by doctor name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <Search size={16} color="var(--text-subtle)" style={{ position: 'absolute', left: '0.85rem', top: '50%', transform: 'translateY(-50%)' }} />
            </div>

            {/* Specialty Select */}
            <select
              className="form-select"
              value={selectedSpecialty}
              onChange={(e) => setSelectedSpecialty(e.target.value)}
            >
              <option value="">All Medical Specialties</option>
              {specialties.map((spec) => (
                <option key={spec} value={spec}>{spec}</option>
              ))}
            </select>

            {/* Max Fee Filter */}
            <select
              className="form-select"
              value={maxFee}
              onChange={(e) => setMaxFee(e.target.value)}
            >
              <option value="">Any Consultation Fee</option>
              <option value="50">Up to $50</option>
              <option value="100">Up to $100</option>
              <option value="150">Up to $150</option>
              <option value="200">Up to $200</option>
            </select>

            {/* Reset / Refresh */}
            {(selectedSpecialty || searchQuery || maxFee) && (
              <button
                onClick={() => { setSelectedSpecialty(''); setSearchQuery(''); setMaxFee(''); }}
                className="btn btn-outline btn-sm"
                style={{ justifySelf: 'start' }}
              >
                Clear Filters
              </button>
            )}
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div style={{
            backgroundColor: 'var(--danger-bg)',
            color: 'var(--danger)',
            border: '1px solid var(--danger-border)',
            borderRadius: 'var(--radius-md)',
            padding: '1.25rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            marginBottom: '2rem'
          }}>
            <AlertCircle size={20} />
            <div style={{ flex: 1 }}>{String(error)}</div>
            <button onClick={loadData} className="btn btn-outline btn-sm">Try Again</button>
          </div>
        )}

        {/* Loading State */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: '4rem 0' }}>
            <div className="animate-spin" style={{
              width: '36px',
              height: '36px',
              border: '3px solid var(--border-medium)',
              borderTopColor: 'var(--primary-700)',
              borderRadius: '50%',
              margin: '0 auto 1rem auto'
            }} />
            <p style={{ color: 'var(--text-muted)' }}>Loading medical providers...</p>
          </div>
        ) : filteredDoctors.length === 0 ? (
          /* Empty State */
          <div className="card" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
            <Stethoscope size={48} color="var(--sage-400)" style={{ margin: '0 auto 1rem auto' }} />
            <h3 style={{ marginBottom: '0.5rem' }}>No doctors found</h3>
            <p style={{ color: 'var(--text-muted)', maxWidth: '420px', margin: '0 auto 1.5rem auto' }}>
              No medical professionals matched your filter criteria. Try adjusting your specialty or search term.
            </p>
            <button
              onClick={() => { setSelectedSpecialty(''); setSearchQuery(''); setMaxFee(''); }}
              className="btn btn-primary btn-sm"
            >
              Reset Filters
            </button>
          </div>
        ) : (
          /* Doctor Cards Grid */
          <div className="grid-3">
            {filteredDoctors.map((doc) => (
              <DoctorCard key={doc.id} doctor={doc} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

