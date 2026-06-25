import { useEffect, useState } from 'react'
import { supabase } from './lib/supabaseClient'
import { Briefcase, Building, MapPin, ExternalLink } from 'lucide-react'
import './index.css'

function App() {
  const [postings, setPostings] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchPostings()

    // Setup realtime subscription
    const subscription = supabase
      .channel('public:postings')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'postings' }, payload => {
        fetchPostings()
      })
      .subscribe()

    return () => {
      supabase.removeChannel(subscription)
    }
  }, [])

  async function fetchPostings() {
    try {
      const { data, error } = await supabase
        .from('postings')
        .select('*')
        .order('fit_score', { ascending: false, nullsFirst: false })
      
      if (error) throw error
      setPostings(data || [])
    } catch (error) {
      console.error('Error fetching postings:', error)
    } finally {
      setLoading(false)
    }
  }

  const getScoreClass = (score) => {
    if (!score) return 'score-none';
    if (score >= 8) return 'score-high';
    if (score >= 6) return 'score-medium';
    return 'score-low';
  }

  return (
    <div className="dashboard-container">
      {/* Header */}
      <header className="dashboard-header">
        <div>
          <h1>Job Intelligence</h1>
          <p>Reviewing your matched postings from the MCP pipeline.</p>
        </div>
        
        <div className="status-badge">
           <div className="status-dot"></div>
           <span className="status-text">Live DB Sync</span>
        </div>
      </header>

      {/* Content */}
      {loading ? (
        <div className="loader">
          <div className="spinner"></div>
        </div>
      ) : (
        <div className="postings-grid">
          {postings.map((job) => (
            <div key={job.id} className="posting-card">
              <div className="card-header">
                <div className={`score-badge ${getScoreClass(job.fit_score)}`}>
                  {job.fit_score ? `${job.fit_score} / 10 Fit` : 'Unscored'}
                </div>
                <span className="resume-variant">{job.resume_variant || 'Pending'}</span>
              </div>
              
              <h2 className="role-title">
                {job.role_title}
              </h2>
              
              <div className="card-details">
                <div className="detail-item">
                  <Building className="detail-icon" />
                  <span>{job.company}</span>
                </div>
                {job.location && (
                  <div className="detail-item">
                    <MapPin className="detail-icon" />
                    <span>{job.location}</span>
                  </div>
                )}
              </div>

              {job.fit_reasoning && (
                <div className="fit-reasoning">
                  {job.fit_reasoning}
                </div>
              )}

              <div className="card-footer">
                <span className="source-label">
                  Via {job.source}
                </span>
                <a 
                  href={job.url} 
                  target="_blank" 
                  rel="noreferrer"
                  className="view-link"
                >
                  View Role <ExternalLink className="detail-icon" />
                </a>
              </div>
            </div>
          ))}
        </div>
      )}
      
      {!loading && postings.length === 0 && (
        <div className="empty-state">
          <Briefcase className="empty-state-icon" />
          <h3>No postings yet</h3>
          <p>Use Antigravity IDE to fetch and score new jobs.</p>
        </div>
      )}
    </div>
  )
}

export default App
