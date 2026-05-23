import { useApi, buildQuery } from '../hooks/useApi';
import { formatNumber, formatPercent, formatDuration, CHART_COLORS } from '../utils/formatters';
import { Phone, AlertTriangle, Star, CheckCircle, Clock, PhoneForwarded } from 'lucide-react';
import { AreaChart, Area, PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { useEffect, useState, useRef } from 'react';

function AnimatedNumber({ value, suffix = '', prefix = '', decimals = 0 }) {
  const [display, setDisplay] = useState(0);
  const ref = useRef(null);
  useEffect(() => {
    const target = typeof value === 'number' ? value : parseFloat(value) || 0;
    const duration = 800;
    const start = performance.now();
    const from = 0;
    const step = (now) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(from + (target - from) * eased);
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [value]);
  return <span>{prefix}{decimals > 0 ? display.toFixed(decimals) : Math.round(display)}{suffix}</span>;
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: '#111827', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, padding: '10px 14px', fontSize: 12 }}>
      <div style={{ fontWeight: 600, marginBottom: 6, color: '#e8ecf4' }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color, display: 'flex', gap: 8, marginBottom: 2 }}>
          <span>{p.name}:</span><span style={{ fontWeight: 600 }}>{typeof p.value === 'number' && p.value < 1 ? formatPercent(p.value) : p.value}</span>
        </div>
      ))}
    </div>
  );
};

export default function Dashboard({ client }) {
  const q = buildQuery('/api/analytics/overview', { client });
  const { data, loading } = useApi(q, [client]);
  const { data: rcData } = useApi(buildQuery('/api/analytics/root-causes', { client }), [client]);
  const { data: escData } = useApi(buildQuery('/api/analytics/escalations', { client }), [client]);

  if (loading || !data) return <div className="page-header"><h1>Loading...</h1></div>;

  const kpis = [
    { label: 'Total Calls', value: data.total_calls, icon: Phone, color: 'teal', suffix: '' },
    { label: 'Escalation Rate', value: (data.escalation_rate * 100), icon: AlertTriangle, color: 'amber', suffix: '%', decimals: 1 },
    { label: 'Avg CSAT', value: data.avg_csat, icon: Star, color: 'purple', suffix: '/5', decimals: 1 },
    { label: 'Resolution Rate', value: (data.resolution_rate * 100), icon: CheckCircle, color: 'blue', suffix: '%', decimals: 1 },
  ];

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>Executive Dashboard</h1>
        <p>Real-time analytics powered by AI-driven call analysis {client !== 'All' ? `• ${client}` : '• All Clients'}</p>
      </div>

      <div className="kpi-grid">
        {kpis.map(kpi => (
          <div key={kpi.label} className={`kpi-card ${kpi.color}`}>
            <div className="kpi-top">
              <span className="kpi-label">{kpi.label}</span>
              <div className={`kpi-icon ${kpi.color}`}><kpi.icon size={18} /></div>
            </div>
            <div className="kpi-value">
              <AnimatedNumber value={kpi.value} suffix={kpi.suffix} decimals={kpi.decimals || 0} />
            </div>
          </div>
        ))}
      </div>

      <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))' }}>
        <div className="kpi-card teal" style={{ padding: '16px 20px' }}>
          <div className="kpi-label" style={{ marginBottom: 6 }}>Avg Duration</div>
          <div className="kpi-value" style={{ fontSize: 20 }}>{formatDuration(data.avg_duration)}</div>
        </div>
        <div className="kpi-card blue" style={{ padding: '16px 20px' }}>
          <div className="kpi-label" style={{ marginBottom: 6 }}>Callbacks</div>
          <div className="kpi-value" style={{ fontSize: 20 }}><AnimatedNumber value={data.callback_count} /></div>
        </div>
        <div className="kpi-card purple" style={{ padding: '16px 20px' }}>
          <div className="kpi-label" style={{ marginBottom: 6 }}>Escalated</div>
          <div className="kpi-value" style={{ fontSize: 20 }}><AnimatedNumber value={data.escalated_count} /></div>
        </div>
        <div className="kpi-card amber" style={{ padding: '16px 20px' }}>
          <div className="kpi-label" style={{ marginBottom: 6 }}>Avg Sentiment</div>
          <div className="kpi-value" style={{ fontSize: 20, color: data.avg_sentiment > 0 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
            {data.avg_sentiment > 0 ? '+' : ''}{data.avg_sentiment?.toFixed(2)}
          </div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header"><span className="card-title">Call Volume & Escalation Trend</span></div>
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={data.trends}>
              <defs>
                <linearGradient id="colorCalls" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#00d4aa" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#00d4aa" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorEsc" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#f59e0b" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="month" tick={{ fill: '#8b95a8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#8b95a8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="calls" stroke="#00d4aa" fill="url(#colorCalls)" strokeWidth={2} name="Calls" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="card-header"><span className="card-title">Root Cause Distribution</span></div>
          {rcData && (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie data={rcData.distribution} dataKey="count" nameKey="category" cx="50%" cy="50%"
                     innerRadius={60} outerRadius={100} paddingAngle={3} strokeWidth={0}>
                  {rcData.distribution.map((_, i) => (
                    <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ fontSize: 11, color: '#8b95a8' }}
                        formatter={(v) => v.replace(/_/g, ' ')} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header"><span className="card-title">CSAT Trend</span></div>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={data.trends}>
              <defs>
                <linearGradient id="colorCsat" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="month" tick={{ fill: '#8b95a8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis domain={[0, 5]} tick={{ fill: '#8b95a8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="avg_csat" stroke="#8b5cf6" fill="url(#colorCsat)" strokeWidth={2} name="Avg CSAT" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="card-header"><span className="card-title">Escalation by Root Cause</span></div>
          {escData && (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={escData.by_root_cause} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis type="number" tick={{ fill: '#8b95a8', fontSize: 11 }} axisLine={false} tickLine={false}
                       tickFormatter={v => formatPercent(v, 0)} />
                <YAxis type="category" dataKey="category" tick={{ fill: '#8b95a8', fontSize: 10 }} width={100}
                       axisLine={false} tickLine={false} tickFormatter={v => v.replace(/_/g, ' ')} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="rate" fill="#f59e0b" radius={[0, 4, 4, 0]} name="Escalation Rate" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {rcData && (
        <div className="card">
          <div className="card-header"><span className="card-title">Top Recurring Issues</span></div>
          <table className="data-table">
            <thead>
              <tr><th>Issue</th><th>Occurrences</th><th>Recurrence Score</th><th>Severity</th></tr>
            </thead>
            <tbody>
              {rcData.top_recurring?.slice(0, 8).map((r, i) => (
                <tr key={i}>
                  <td style={{ color: 'var(--text-primary)' }}>{r.cause}</td>
                  <td><span style={{ fontWeight: 600 }}>{r.count}</span></td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div className="progress-bar" style={{ width: 80 }}>
                        <div className="progress-bar-fill" style={{ width: `${r.recurrence_score * 100}%`,
                             background: r.recurrence_score > 0.7 ? 'var(--accent-red)' : r.recurrence_score > 0.4 ? 'var(--accent-amber)' : 'var(--accent-green)' }} />
                      </div>
                      <span>{r.recurrence_score}</span>
                    </div>
                  </td>
                  <td>
                    <span className={`badge ${r.recurrence_score > 0.7 ? 'red' : r.recurrence_score > 0.4 ? 'amber' : 'green'}`}>
                      {r.recurrence_score > 0.7 ? 'Critical' : r.recurrence_score > 0.4 ? 'Medium' : 'Low'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
