import { useEffect, useState } from 'react'
import { supabase } from './lib/supabaseClient'
import { ClipboardList, Calendar, ArrowRight } from 'lucide-react'

export default function Tracker() {
  const [applications, setApplications] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchApplications()

    const subscription = supabase
      .channel('public:applications')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'applications' }, payload => {
        fetchApplications()
      })
      .subscribe()

    return () => {
      supabase.removeChannel(subscription)
    }
  }, [])

  async function fetchApplications() {
    try {
      const { data, error } = await supabase
        .from('applications')
        .select('*, postings(role_title, company, url)')
        .order('applied_at', { ascending: false })
      
      if (error) throw error
      setApplications(data || [])
    } catch (error) {
      console.error('Error fetching applications:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status) => {
    switch(status) {
      case 'applied': return 'bg-blue-900/50 text-blue-400 border-blue-800';
      case 'interview_scheduled':
      case 'interviewed': return 'bg-purple-900/50 text-purple-400 border-purple-800';
      case 'offer': return 'bg-emerald-900/50 text-emerald-400 border-emerald-800';
      case 'rejected':
      case 'ghosted': return 'bg-red-900/50 text-red-400 border-red-800';
      default: return 'bg-gray-800 text-gray-300 border-gray-700';
    }
  }

  return (
    <div className="postings-grid">
      {loading ? (
        <div className="loader"><div className="spinner"></div></div>
      ) : applications.map(app => (
        <div key={app.id} className="posting-card">
          <div className="card-header">
            <div className={`px-3 py-1 rounded-full text-xs font-semibold border ${getStatusColor(app.status)}`}>
              {app.status.replace('_', ' ').toUpperCase()}
            </div>
            <span className="resume-variant">{new Date(app.applied_at).toLocaleDateString()}</span>
          </div>
          
          <h2 className="role-title text-white">
            {app.postings?.role_title}
          </h2>
          
          <div className="card-details mb-4">
            <div className="detail-item">
              <span>{app.postings?.company}</span>
            </div>
            <div className="detail-item text-xs text-gray-500">
              Resume: {app.resume_version}
            </div>
          </div>

          <div className="fit-reasoning flex-grow">
            {app.next_action ? (
              <div>
                <span className="text-xs text-gray-500 uppercase tracking-wider mb-2 block">Next Action</span>
                <div style={{display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#d1d5db'}}>
                  <ArrowRight size={14} style={{color: '#818cf8'}}/> {app.next_action}
                </div>
                {app.next_action_date && (
                  <div style={{display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#9ca3af', marginTop: '0.5rem', fontSize: '0.75rem'}}>
                    <Calendar size={12}/> Due: {app.next_action_date}
                  </div>
                )}
              </div>
            ) : (
              <span style={{color: '#4b5563', fontStyle: 'italic'}}>No next action set.</span>
            )}
          </div>
        </div>
      ))}
      
      {!loading && applications.length === 0 && (
        <div className="empty-state" style={{gridColumn: '1 / -1'}}>
          <ClipboardList className="empty-state-icon" />
          <h3>No applications tracked yet</h3>
          <p>Use Antigravity IDE to create an application from a shortlisted job.</p>
        </div>
      )}
    </div>
  )
}
