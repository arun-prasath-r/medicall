import React, { useState, useEffect } from 'react';
import { adminService } from '../services/adminService';
import { 
  ShieldCheck, 
  AlertCircle, 
  CheckCircle2, 
  Stethoscope, 
  Award, 
  Clock, 
  RefreshCw 
} from 'lucide-react';
import { formatApiError } from '../utils/errorUtils';

export const AdminVerificationPage = () => {
  const [activeTab, setActiveTab] = useState('PENDING'); // 'PENDING' | 'ALL'
  const [pendingDoctors, setPendingDoctors] = useState([]);
  const [allDoctors, setAllDoctors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoadingId, setActionLoadingId] = useState(null);
  const [statusMsg, setStatusMsg] = useState({ type: '', text: '' });

  const loadData = async () => {
    setLoading(true);
    try {
      const [pending, all] = await Promise.all([
        adminService.getPendingDoctors(),
        adminService.getAllDoctors()
      ]);
      setPendingDoctors(pending);
      setAllDoctors(all);
    } catch (err) {
      console.error('Error fetching admin doctor lists:', err);
      setStatusMsg({ type: 'error', text: 'Failed to retrieve doctor verification records.' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleApprove = async (doctorId, doctorName) => {
    setActionLoadingId(doctorId);
    setStatusMsg({ type: '', text: '' });
    try {
      const resp = await adminService.verifyDoctor(doctorId);
      setStatusMsg({
        type: 'success',
        text: `Successfully approved medical license for Dr. ${doctorName}. Profile is now publicly verified.`
      });
      // Refresh local lists
      await loadData();
    } catch (err) {
      console.error('Error approving doctor:', err);
      setStatusMsg({ type: 'error', text: formatApiError(err, 'Approval failed.') });
    } finally {
      setActionLoadingId(null);
    }
  };

  const displayedDoctors = activeTab === 'PENDING' ? pendingDoctors : allDoctors;

  return (
    <div className="page-wrapper">
      <div className="container">
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
              <span className="badge badge-neutral"><ShieldCheck size={14} /> System Administration</span>
            </div>
            <h2>Doctor Credential Verification Portal</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
              Review state medical board licenses and activate practitioner consultation capabilities.
            </p>
          </div>
          <button onClick={loadData} className="btn btn-outline btn-sm" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <RefreshCw size={14} />
            <span>Refresh</span>
          </button>
        </div>

        {/* Status Message */}
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

        {/* Tab Toggle */}
        <div style={{
          display: 'flex',
          gap: '0.5rem',
          padding: '0.25rem',
          backgroundColor: 'var(--bg-subtle)',
          borderRadius: 'var(--radius-md)',
          width: 'fit-content',
          marginBottom: '2rem'
        }}>
          <button
            onClick={() => setActiveTab('PENDING')}
            style={{
              padding: '0.5rem 1.25rem',
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              fontWeight: 600,
              fontSize: '0.88rem',
              cursor: 'pointer',
              backgroundColor: activeTab === 'PENDING' ? 'var(--bg-surface)' : 'transparent',
              color: activeTab === 'PENDING' ? 'var(--primary-800)' : 'var(--text-muted)',
              boxShadow: activeTab === 'PENDING' ? 'var(--shadow-xs)' : 'none'
            }}
          >
            Pending Verification ({pendingDoctors.length})
          </button>
          <button
            onClick={() => setActiveTab('ALL')}
            style={{
              padding: '0.5rem 1.25rem',
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              fontWeight: 600,
              fontSize: '0.88rem',
              cursor: 'pointer',
              backgroundColor: activeTab === 'ALL' ? 'var(--bg-surface)' : 'transparent',
              color: activeTab === 'ALL' ? 'var(--primary-800)' : 'var(--text-muted)',
              boxShadow: activeTab === 'ALL' ? 'var(--shadow-xs)' : 'none'
            }}
          >
            All Practitioners ({allDoctors.length})
          </button>
        </div>

        {/* List of Doctors */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: '4rem 0' }}>
            <div className="animate-spin" style={{ width: '36px', height: '36px', border: '3px solid var(--border-medium)', borderTopColor: 'var(--primary-700)', borderRadius: '50%', margin: '0 auto 1rem auto' }} />
            <p style={{ color: 'var(--text-muted)' }}>Retrieving doctor credentials...</p>
          </div>
        ) : displayedDoctors.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', padding: '3.5rem 2rem' }}>
            <CheckCircle2 size={44} color="var(--success)" style={{ margin: '0 auto 0.75rem auto' }} />
            <h4>No Pending Verifications</h4>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              All registered doctors have been reviewed and approved.
            </p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {displayedDoctors.map((doc) => (
              <div key={doc.id} className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1.5rem' }}>
                <div style={{ flex: 1, minWidth: '280px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.35rem' }}>
                    <h3 style={{ fontSize: '1.2rem', color: 'var(--primary-900)' }}>
                      Dr. {doc.first_name} {doc.last_name}
                    </h3>
                    {doc.is_verified ? (
                      <span className="badge badge-success"><ShieldCheck size={12} /> Verified</span>
                    ) : (
                      <span className="badge badge-warning"><Clock size={12} /> Pending Review</span>
                    )}
                  </div>

                  <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', fontSize: '0.88rem', color: 'var(--text-body)', marginTop: '0.5rem' }}>
                    <div>
                      <span style={{ color: 'var(--text-muted)' }}>Specialty:</span> <strong>{doc.specialty}</strong>
                    </div>
                    <div>
                      <span style={{ color: 'var(--text-muted)' }}>License:</span> <strong style={{ fontFamily: 'monospace' }}>{doc.license_number}</strong>
                    </div>
                    <div>
                      <span style={{ color: 'var(--text-muted)' }}>Qualifications:</span> {doc.qualifications}
                    </div>
                    <div>
                      <span style={{ color: 'var(--text-muted)' }}>Experience:</span> {doc.experience_years} Years
                    </div>
                  </div>

                  {doc.bio && (
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.5rem', maxWidth: '640px' }}>
                      {doc.bio}
                    </p>
                  )}
                </div>

                <div>
                  {!doc.is_verified ? (
                    <button
                      onClick={() => handleApprove(doc.id, `${doc.first_name} ${doc.last_name}`)}
                      className="btn btn-primary"
                      disabled={actionLoadingId === doc.id}
                      style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
                    >
                      <ShieldCheck size={16} />
                      <span>{actionLoadingId === doc.id ? 'Approving...' : 'Approve Doctor'}</span>
                    </button>
                  ) : (
                    <span style={{ fontSize: '0.85rem', color: 'var(--success)', fontWeight: 600 }}>
                      &check; License Approved
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

