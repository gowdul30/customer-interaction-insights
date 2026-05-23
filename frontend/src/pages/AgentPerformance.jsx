import { useApi, buildQuery } from '../hooks/useApi';
import { formatPercent } from '../utils/formatters';
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import { Trophy, TrendingUp, TrendingDown } from 'lucide-react';

export default function AgentPerformance({ client }) {
  const { data, loading } = useApi(buildQuery('/api/analytics/agents', { client }), [client]);

  if (loading || !data) return <div className="page-header"><h1>Loading...</h1></div>;

  const top5 = data.leaderboard.slice(0, 5);
  const bottom3 = data.leaderboard.slice(-3).reverse();
  const selectedAgent = top5[0];

  const radarData = selectedAgent ? [
    { metric: 'Resolution', value: selectedAgent.resolution_rate * 100, fullMark: 100 },
    { metric: 'CSAT', value: selectedAgent.avg_csat * 20, fullMark: 100 },
    { metric: 'Low Escalation', value: (1 - selectedAgent.escalation_rate) * 100, fullMark: 100 },
    { metric: 'Sentiment', value: ((selectedAgent.avg_sentiment + 1) / 2) * 100, fullMark: 100 },
    { metric: 'Quality', value: selectedAgent.quality_score * 100, fullMark: 100 },
  ] : [];

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>Agent Performance</h1>
        <p>AI-generated quality scores and coaching recommendations {client !== 'All' ? `• ${client}` : ''}</p>
      </div>

      <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)', marginBottom: 24 }}>
        <div className="kpi-card teal">
          <div className="kpi-label" style={{ marginBottom: 8 }}>Total Agents</div>
          <div className="kpi-value">{data.total_agents}</div>
        </div>
        <div className="kpi-card purple">
          <div className="kpi-label" style={{ marginBottom: 8 }}>Top Performer</div>
          <div className="kpi-value" style={{ fontSize: 18 }}>{top5[0]?.agent_name || 'N/A'}</div>
        </div>
        <div className="kpi-card blue">
          <div className="kpi-label" style={{ marginBottom: 8 }}>Avg Quality Score</div>
          <div className="kpi-value">
            {(data.leaderboard.reduce((s, a) => s + a.quality_score, 0) / data.leaderboard.length).toFixed(2)}
          </div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header"><span className="card-title">🏆 Top Agent Radar — {selectedAgent?.agent_name}</span></div>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="rgba(255,255,255,0.08)" />
              <PolarAngleAxis dataKey="metric" tick={{ fill: '#8b95a8', fontSize: 11 }} />
              <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
              <Radar dataKey="value" stroke="#00d4aa" fill="#00d4aa" fillOpacity={0.2} strokeWidth={2} />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="card-header"><span className="card-title">Quality Score Distribution</span></div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data.leaderboard.slice(0, 12)}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="agent_name" tick={{ fill: '#8b95a8', fontSize: 9 }} axisLine={false} tickLine={false}
                     angle={-30} textAnchor="end" height={60}
                     tickFormatter={v => v.split(' ')[0]} />
              <YAxis domain={[0, 1]} tick={{ fill: '#8b95a8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: '#111827', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }} />
              <Bar dataKey="quality_score" name="Quality Score" radius={[6, 6, 0, 0]} fill="#8b5cf6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <span className="card-title"><TrendingUp size={16} style={{ color: 'var(--accent-green)', marginRight: 6 }} />Top Performers</span>
          </div>
          <table className="data-table">
            <thead><tr><th>Rank</th><th>Agent</th><th>Quality</th><th>Resolution</th><th>CSAT</th><th>Calls</th></tr></thead>
            <tbody>
              {top5.map((a, i) => (
                <tr key={a.agent_id}>
                  <td><span className="badge teal">{i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `#${i+1}`}</span></td>
                  <td style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{a.agent_name}</td>
                  <td style={{ color: 'var(--accent-teal)', fontWeight: 700 }}>{a.quality_score.toFixed(2)}</td>
                  <td>{formatPercent(a.resolution_rate)}</td>
                  <td style={{ color: a.avg_csat >= 4 ? 'var(--accent-green)' : 'var(--accent-amber)' }}>{a.avg_csat}</td>
                  <td>{a.total_calls}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title"><TrendingDown size={16} style={{ color: 'var(--accent-red)', marginRight: 6 }} />Needs Coaching</span>
          </div>
          <table className="data-table">
            <thead><tr><th>Agent</th><th>Quality</th><th>Escalation</th><th>CSAT</th><th>Action</th></tr></thead>
            <tbody>
              {bottom3.map(a => (
                <tr key={a.agent_id}>
                  <td style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{a.agent_name}</td>
                  <td style={{ color: 'var(--accent-red)', fontWeight: 700 }}>{a.quality_score.toFixed(2)}</td>
                  <td><span className="badge red">{formatPercent(a.escalation_rate)}</span></td>
                  <td>{a.avg_csat}</td>
                  <td><span className="badge purple">Schedule Training</span></td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ marginTop: 16, padding: '12px 16px', background: 'rgba(139,92,246,0.08)', borderRadius: 8, fontSize: 12, color: 'var(--text-secondary)' }}>
            💡 <strong style={{ color: 'var(--accent-purple)' }}>AI Recommendation:</strong> Pair bottom performers with top agents for mentoring. Focus on de-escalation techniques and first-call resolution strategies.
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header"><span className="card-title">Full Agent Leaderboard</span></div>
        <table className="data-table">
          <thead>
            <tr><th>#</th><th>Agent</th><th>Quality</th><th>Calls</th><th>Resolution</th><th>Escalation</th><th>CSAT</th><th>Avg Sentiment</th><th>Avg Duration</th></tr>
          </thead>
          <tbody>
            {data.leaderboard.map((a, i) => (
              <tr key={a.agent_id}>
                <td>{i + 1}</td>
                <td style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{a.agent_name}</td>
                <td style={{ fontWeight: 700, color: a.quality_score > 0.7 ? 'var(--accent-green)' : a.quality_score > 0.5 ? 'var(--accent-amber)' : 'var(--accent-red)' }}>
                  {a.quality_score.toFixed(3)}
                </td>
                <td>{a.total_calls}</td>
                <td>{formatPercent(a.resolution_rate)}</td>
                <td><span className={`badge ${a.escalation_rate > 0.5 ? 'red' : a.escalation_rate > 0.3 ? 'amber' : 'green'}`}>{formatPercent(a.escalation_rate)}</span></td>
                <td>{a.avg_csat}</td>
                <td style={{ color: a.avg_sentiment > 0 ? 'var(--accent-green)' : 'var(--accent-red)' }}>{a.avg_sentiment.toFixed(2)}</td>
                <td>{Math.round(a.avg_duration / 60)}m</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
