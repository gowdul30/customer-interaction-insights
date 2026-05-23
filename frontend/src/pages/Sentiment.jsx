import { useApi, buildQuery } from '../hooks/useApi';
import { CHART_COLORS, formatPercent } from '../utils/formatters';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, ScatterChart, Scatter, ZAxis, PieChart, Pie, Cell, Legend } from 'recharts';

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: '#111827', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, padding: '10px 14px', fontSize: 12 }}>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color || '#e8ecf4', display: 'flex', gap: 8, marginBottom: 2 }}>
          <span>{p.name}:</span><span style={{ fontWeight: 600 }}>{typeof p.value === 'number' ? p.value.toFixed(2) : p.value}</span>
        </div>
      ))}
    </div>
  );
};

const TONE_COLORS = { satisfied: '#22c55e', neutral: '#3b82f6', frustrated: '#f59e0b', angry: '#ef4444' };
const BUCKET_COLORS = { very_negative: '#ef4444', negative: '#f59e0b', neutral: '#3b82f6', positive: '#22c55e', very_positive: '#00d4aa' };

export default function Sentiment({ client }) {
  const { data, loading } = useApi(buildQuery('/api/analytics/sentiment', { client }), [client]);

  if (loading || !data) return <div className="page-header"><h1>Loading...</h1></div>;

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>Sentiment Analysis</h1>
        <p>AI-powered tone detection and customer emotion tracking {client !== 'All' ? `• ${client}` : ''}</p>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header"><span className="card-title">Tone Distribution</span></div>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={data.distribution} dataKey="count" nameKey="tone" cx="50%" cy="50%"
                   innerRadius={70} outerRadius={110} paddingAngle={3} strokeWidth={0}>
                {data.distribution.map((d, i) => (
                  <Cell key={i} fill={TONE_COLORS[d.tone] || CHART_COLORS[i]} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="card-header"><span className="card-title">Sentiment Score Distribution</span></div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data.score_distribution}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="bucket" tick={{ fill: '#8b95a8', fontSize: 10 }} axisLine={false} tickLine={false}
                     tickFormatter={v => v.replace(/_/g, ' ')} />
              <YAxis tick={{ fill: '#8b95a8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="count" name="Calls" radius={[6, 6, 0, 0]}>
                {data.score_distribution.map((d, i) => (
                  <Cell key={i} fill={BUCKET_COLORS[d.bucket] || '#3b82f6'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header"><span className="card-title">Monthly Sentiment Trend</span></div>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={data.trends}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="month" tick={{ fill: '#8b95a8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis domain={[-1, 1]} tick={{ fill: '#8b95a8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Line type="monotone" dataKey="avg_sentiment" stroke="#00d4aa" strokeWidth={2} dot={{ r: 4 }} name="Avg Sentiment" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="card-header"><span className="card-title">Sentiment vs CSAT Correlation</span></div>
          <ResponsiveContainer width="100%" height={280}>
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis type="number" dataKey="sentiment_score" name="Sentiment" domain={[-1, 1]}
                     tick={{ fill: '#8b95a8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis type="number" dataKey="csat_score" name="CSAT" domain={[0, 5]}
                     tick={{ fill: '#8b95a8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Scatter data={data.csat_correlation} fill="#8b5cf6" fillOpacity={0.6} name="Calls" />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card">
        <div className="card-header"><span className="card-title">Sentiment by Client</span></div>
        <table className="data-table">
          <thead><tr><th>Client</th><th>Avg Sentiment</th><th>Total Calls</th><th>Indicator</th></tr></thead>
          <tbody>
            {data.by_client?.map((c, i) => (
              <tr key={i}>
                <td style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{c.client}</td>
                <td style={{ color: c.avg_sentiment > 0 ? 'var(--accent-green)' : 'var(--accent-red)', fontWeight: 600 }}>
                  {c.avg_sentiment > 0 ? '+' : ''}{c.avg_sentiment.toFixed(3)}
                </td>
                <td>{c.count}</td>
                <td>
                  <div className="progress-bar" style={{ width: 100 }}>
                    <div className="progress-bar-fill" style={{
                      width: `${((c.avg_sentiment + 1) / 2) * 100}%`,
                      background: c.avg_sentiment > 0 ? 'var(--accent-green)' : c.avg_sentiment > -0.3 ? 'var(--accent-amber)' : 'var(--accent-red)'
                    }} />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
