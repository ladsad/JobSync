import { useState } from 'react'
import Dashboard from './Dashboard'
import Outreach from './Outreach'
import './index.css'

function App() {
  const [activeTab, setActiveTab] = useState('dashboard')

  return (
    <div className="dashboard-container">
      {/* Header */}
      <header className="dashboard-header" style={{flexDirection: 'column', alignItems: 'flex-start', gap: '1.5rem'}}>
        <div style={{display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center'}}>
          <div>
            <h1>Job Intelligence</h1>
            <p>Reviewing your matched postings and outreach from the MCP pipeline.</p>
          </div>
          
          <div className="status-badge">
             <div className="status-dot"></div>
             <span className="status-text">Live DB Sync</span>
          </div>
        </div>
        
        <div style={{display: 'flex', gap: '1rem', borderBottom: '1px solid var(--border-color)', width: '100%'}}>
          <button 
            onClick={() => setActiveTab('dashboard')}
            style={{
              background: 'none', border: 'none', 
              color: activeTab === 'dashboard' ? 'var(--accent-color)' : 'var(--text-secondary)', 
              padding: '0.5rem 1rem', cursor: 'pointer', fontSize: '1rem', fontWeight: 500,
              borderBottom: activeTab === 'dashboard' ? '2px solid var(--accent-color)' : '2px solid transparent',
              transition: 'all 0.2s ease'
            }}
          >
            Job Matches
          </button>
          <button 
            onClick={() => setActiveTab('outreach')}
            style={{
              background: 'none', border: 'none', 
              color: activeTab === 'outreach' ? 'var(--accent-color)' : 'var(--text-secondary)', 
              padding: '0.5rem 1rem', cursor: 'pointer', fontSize: '1rem', fontWeight: 500,
              borderBottom: activeTab === 'outreach' ? '2px solid var(--accent-color)' : '2px solid transparent',
              transition: 'all 0.2s ease'
            }}
          >
            Outreach
          </button>
        </div>
      </header>

      {/* Content */}
      {activeTab === 'dashboard' ? <Dashboard /> : <Outreach />}
    </div>
  )
}

export default App
