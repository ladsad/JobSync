import { useEffect, useState } from 'react'
import { supabase } from './lib/supabaseClient'
import { Users, Send, CheckCircle, Linkedin } from 'lucide-react'

export default function Outreach() {
  const [contacts, setContacts] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchContacts()

    const subscription = supabase
      .channel('public:contacts')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'contacts' }, payload => {
        fetchContacts()
      })
      .subscribe()

    return () => {
      supabase.removeChannel(subscription)
    }
  }, [])

  async function fetchContacts() {
    try {
      const { data, error } = await supabase
        .from('contacts')
        .select('*')
        .order('id', { ascending: false })
      
      if (error) throw error
      setContacts(data || [])
    } catch (error) {
      console.error('Error fetching contacts:', error)
    } finally {
      setLoading(false)
    }
  }

  async function markAsSent(id) {
    try {
      await supabase.from('contacts').update({ message_sent: true }).eq('id', id)
    } catch (e) {
      console.error(e)
    }
  }

  return (
    <div className="postings-grid">
      {loading ? (
        <div className="loader"><div className="spinner"></div></div>
      ) : contacts.map(contact => (
        <div key={contact.id} className="posting-card">
          <div className="card-header">
            <div className={`score-badge ${contact.message_sent ? 'score-high' : 'score-low'}`}>
              {contact.message_sent ? 'Sent' : 'Drafted'}
            </div>
            <span className="resume-variant">{contact.relation}</span>
          </div>
          
          <h2 className="role-title text-white flex items-center gap-2" style={{display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
            {contact.name}
            {contact.linkedin_url && (
              <a href={contact.linkedin_url} target="_blank" rel="noreferrer" style={{color: '#3b82f6', display: 'flex'}}>
                <Linkedin size={16} />
              </a>
            )}
          </h2>
          
          <div className="card-details" style={{marginBottom: '1rem'}}>
            <div className="detail-item">
              <span>{contact.company}</span>
            </div>
          </div>

          <div className="fit-reasoning" style={{flexGrow: 1, whiteSpace: 'pre-wrap'}}>
            {contact.message_draft || "No draft generated yet."}
          </div>

          <div className="card-footer" style={{borderTop: 'none', paddingTop: 0}}>
            {!contact.message_sent && contact.message_draft && (
              <button 
                onClick={() => markAsSent(contact.id)}
                style={{
                  display: 'flex', alignItems: 'center', gap: '0.5rem', background: '#4f46e5', 
                  color: 'white', border: 'none', padding: '0.5rem 1rem', borderRadius: '0.5rem',
                  cursor: 'pointer', fontSize: '0.875rem'
                }}
              >
                <Send size={16} /> Mark as Sent
              </button>
            )}
            {contact.message_sent && (
              <div style={{display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#34d399', fontSize: '0.875rem'}}>
                <CheckCircle size={16} /> Message Sent
              </div>
            )}
          </div>
        </div>
      ))}
      
      {!loading && contacts.length === 0 && (
        <div className="empty-state" style={{gridColumn: '1 / -1'}}>
          <Users className="empty-state-icon" />
          <h3>No contacts yet</h3>
          <p>Use Antigravity IDE to add contacts and draft messages.</p>
        </div>
      )}
    </div>
  )
}
