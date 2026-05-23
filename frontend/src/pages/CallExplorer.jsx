import { useState } from 'react';
import { useApi, buildQuery } from '../hooks/useApi';
import { formatDuration, toneEmoji } from '../utils/formatters';
import { Search, X, Phone, Clock, User, AlertTriangle, MessageSquare } from 'lucide-react';

function CallDetail({ call, onClose }) {
  if (!call) return null;
  const m = call.call_metadata;
  const n = call.nlp_analysis;
  const f = call.feedback;

  return (
    <>
      <div className="detail-panel-overlay" onClick={onClose} />
      <div className="detail-panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <div>
            <h2 style={{ fontSize: 18, fontWeight: 700 }}>{call.call_id}</h2>
            <span className="badge blue" style={{ marginTop: 4 }}>{call.client}</span>
          </div>
          <button className="detail-close" onClick={onClose}><X size={20} /></button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 20 }}>
          <div style={{ padding: 12, background: 'rgba(255,255,255,0.03)', borderRadius: 8 }}>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>Date</div>
            <div style={{ fontWeight: 600, fontSize: 13 }}>{m.date} {m.time}</div>
          </div>
          <div style={{ padding: 12, background: 'rgba(255,255,255,0.03)', borderRadius: 8 }}>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>Duration</div>
            <div style={{ fontWeight: 600, fontSize: 13 }}>{formatDuration(m.duration_seconds)}</div>
          </div>
          <div style={{ padding: 12, background: 'rgba(255,255,255,0.03)', borderRadius: 8 }}>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>Agent</div>
            <div style={{ fontWeight: 600, fontSize: 13 }}>{m.agent_name}</div>
          </div>
          <div style={{ padding: 12, background: 'rgba(255,255,255,0.03)', borderRadius: 8 }}>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>Resolved</div>
            <span className={`badge ${m.issue_resolved ? 'green' : 'red'}`}>{m.issue_resolved ? 'Yes' : 'No'}</span>
          </div>
        </div>

        <div style={{ marginBottom: 20 }}>
          <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: 'var(--accent-teal)' }}>📝 Transcript Summary</h3>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.7 }}>{call.transcript_summary}</p>
        </div>

        <div style={{ marginBottom: 20 }}>
          <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: 'var(--accent-blue)' }}>🔍 NLP Analysis</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: 'rgba(255,255,255,0.03)', borderRadius: 6 }}>
              <span style={{ color: 'var(--text-muted)' }}>Primary Intent</span>
              <span className="badge teal">{n.customer_intent.primary_intent.replace(/_/g, ' ')}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: 'rgba(255,255,255,0.03)', borderRadius: 6 }}>
              <span style={{ color: 'var(--text-muted)' }}>Root Cause</span>
              <span className="badge purple">{n.root_cause.category.replace(/_/g, ' ')}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: 'rgba(255,255,255,0.03)', borderRadius: 6 }}>
              <span style={{ color: 'var(--text-muted)' }}>Escalated</span>
              <span className={`badge ${n.escalation.escalated ? 'red' : 'green'}`}>{n.escalation.escalated ? 'Yes' : 'No'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: 'rgba(255,255,255,0.03)', borderRadius: 6 }}>
              <span style={{ color: 'var(--text-muted)' }}>Tone</span>
              <span>{toneEmoji(n.customer_tone.overall)} {n.customer_tone.overall}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: 'rgba(255,255,255,0.03)', borderRadius: 6 }}>
              <span style={{ color: 'var(--text-muted)' }}>Sentiment Score</span>
              <span style={{ fontWeight: 700, color: n.customer_tone.sentiment_score > 0 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                {n.customer_tone.sentiment_score > 0 ? '+' : ''}{n.customer_tone.sentiment_score}
              </span>
            </div>
          </div>
        </div>

        {n.customer_tone.tone_progression && (
          <div style={{ marginBottom: 20 }}>
            <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: 'var(--accent-purple)' }}>😤 Tone Progression</h3>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              {n.customer_tone.tone_progression.map((t, i) => (
                <span key={i} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <span className="badge blue">{toneEmoji(t)} {t}</span>
                  {i < n.customer_tone.tone_progression.length - 1 && <span style={{ color: 'var(--text-muted)' }}>→</span>}
                </span>
              ))}
            </div>
          </div>
        )}

        {f.post_call_survey_completed && (
          <div style={{ padding: 14, background: 'rgba(255,255,255,0.03)', borderRadius: 8 }}>
            <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: 'var(--accent-amber)' }}>⭐ Feedback</h3>
            <div style={{ fontSize: 20, fontWeight: 800, marginBottom: 6 }}>{'⭐'.repeat(f.csat_score)}<span style={{ opacity: 0.2 }}>{'⭐'.repeat(5 - f.csat_score)}</span></div>
            {f.customer_comment && <p style={{ fontSize: 12, color: 'var(--text-secondary)', fontStyle: 'italic' }}>"{f.customer_comment}"</p>}
          </div>
        )}
      </div>
    </>
  );
}

export default function CallExplorer({ client }) {
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState(null);

  const query = buildQuery('/api/calls', { client, search: search || undefined, page, limit: 15 });
  const { data, loading } = useApi(query, [client, search, page]);

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>Call Explorer</h1>
        <p>Browse and search individual call records with AI-extracted insights</p>
      </div>

      <div className="card" style={{ marginBottom: 20 }}>
        <div className="search-wrapper">
          <Search size={16} />
          <input className="search-input" placeholder="Search by call ID, agent name, root cause, or keyword..."
                 value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} />
        </div>
      </div>

      <div className="card">
        {loading ? <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>Loading...</div> : (
          <>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 16 }}>{data?.total || 0} calls found</div>
            <table className="data-table">
              <thead>
                <tr><th>Call ID</th><th>Client</th><th>Date</th><th>Agent</th><th>Root Cause</th><th>Tone</th><th>Resolved</th><th>CSAT</th></tr>
              </thead>
              <tbody>
                {data?.calls?.map(c => (
                  <tr key={c.call_id} onClick={() => setSelected(c)} style={{ cursor: 'pointer' }}>
                    <td style={{ color: 'var(--accent-teal)', fontWeight: 600 }}>{c.call_id}</td>
                    <td>{c.client}</td>
                    <td>{c.call_metadata.date}</td>
                    <td>{c.call_metadata.agent_name}</td>
                    <td><span className="badge purple">{c.nlp_analysis.root_cause.category.replace(/_/g, ' ')}</span></td>
                    <td>{toneEmoji(c.nlp_analysis.customer_tone.overall)} {c.nlp_analysis.customer_tone.overall}</td>
                    <td><span className={`badge ${c.call_metadata.issue_resolved ? 'green' : 'red'}`}>
                      {c.call_metadata.issue_resolved ? 'Yes' : 'No'}</span></td>
                    <td>{c.feedback.post_call_survey_completed ? `${c.feedback.csat_score}/5` : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            {data?.pages > 1 && (
              <div className="pagination">
                <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}>Previous</button>
                <span>Page {page} of {data.pages}</span>
                <button disabled={page >= data.pages} onClick={() => setPage(p => p + 1)}>Next</button>
              </div>
            )}
          </>
        )}
      </div>

      {selected && <CallDetail call={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}
