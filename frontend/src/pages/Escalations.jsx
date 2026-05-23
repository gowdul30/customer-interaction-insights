import { useApi, buildQuery } from '../hooks/useApi';
import { formatPercent, CHART_COLORS } from '../utils/formatters';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, Legend } from 'recharts';

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: '#111827', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, padding: '10px 14px', fontSize: 12 }}>
      <div style={{ fontWeight: 600, marginBottom: 6, color: '#e8ecf4' }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color, display: 'flex', gap: 8, marginBottom: 2 }}>
          <span>{p.name}:</span>
          <span style={{ fontWeight: 600 }}>{typeof p.value === 'number' && p.value < 1 ? formatPercent(p.value) : p.value}</span>
        </div>
      ))}
    </div>
  );
};

export default function Escalations({ client }) {
  const { data, loading } = useApi(buildQuery('/api/analytics/escalations', { client }), [client]);

  if (loading || !data) return <div className="page-header"><h1>Loading...</h1></div>;

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>Escalation Analytics</h1>
        <p>AI-predicted escalation patterns and driver analysis {client !== 'All' ? `• ${client}` : ''}</p>
      </div>

      <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)', marginBottom: 24 }}>
        <div className="kpi-card amber">
          <div className="kpi-label" style={{ marginBottom: 8 }}>Total Escalated</div>
          <div className="kpi-value">{data.total_escalated}</div>
        </div>
        <div className="kpi-card red" style={{ '--before-bg': 'var(--gradient-warm)' }}>
          <div className="kpi-label" style={{ marginBottom: 8 }}>Escalation Rate</div>
          <div className="kpi-value">{formatPercent(data.escalation_rate)}</div>
        </div>
        <div className="kpi-card purple">
          <div className="kpi-label" style={{ marginBottom: 8 }}>Avg per Month</div>
          <div className="kpi-value">{Math.round(data.total_escalated / (data.trends?.length || 1))}</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header"><span className="card-title">Escalation Rate by Client</span></div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={data.by_client}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="client" tick={{ fill: '#8b95a8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tickFormatter={v => formatPercent(v, 0)} tick={{ fill: '#8b95a8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="rate" name="Escalation Rate" radius={[6, 6, 0, 0]}>
                {data.by_client.map((_, i) => (
                  <rect key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="card-header"><span className="card-title">Top Escalation Signals</span></div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={data.top_signals} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis type="number" tick={{ fill: '#8b95a8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="signal" tick={{ fill: '#8b95a8', fontSize: 10 }} width={160}
                     axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="count" fill="#ef4444" radius={[0, 6, 6, 0]} name="Occurrences" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header"><span className="card-title">Monthly Escalation Trend</span></div>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={data.trends}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="month" tick={{ fill: '#8b95a8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tickFormatter={v => formatPercent(v, 0)} tick={{ fill: '#8b95a8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Line type="monotone" dataKey="rate" stroke="#f59e0b" strokeWidth={2} dot={{ r: 4 }} name="Escalation Rate" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="card-header"><span className="card-title">Escalation by Root Cause</span></div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={data.by_root_cause} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis type="number" tickFormatter={v => formatPercent(v, 0)} tick={{ fill: '#8b95a8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="category" tick={{ fill: '#8b95a8', fontSize: 10 }} width={110}
                     axisLine={false} tickLine={false} tickFormatter={v => v.replace(/_/g, ' ')} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="rate" fill="#8b5cf6" radius={[0, 6, 6, 0]} name="Escalation Rate" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
