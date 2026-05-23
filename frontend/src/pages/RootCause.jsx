import { useApi, buildQuery } from '../hooks/useApi';
import { formatPercent, CHART_COLORS } from '../utils/formatters';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Treemap, AreaChart, Area, Legend } from 'recharts';

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: '#111827', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, padding: '10px 14px', fontSize: 12 }}>
      <div style={{ fontWeight: 600, marginBottom: 6, color: '#e8ecf4' }}>{label || payload[0]?.payload?.category}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color || '#e8ecf4', display: 'flex', gap: 8, marginBottom: 2 }}>
          <span>{p.name || 'Count'}:</span><span style={{ fontWeight: 600 }}>{p.value}</span>
        </div>
      ))}
    </div>
  );
};

const TreemapContent = ({ x, y, width, height, name, count }) => {
  if (width < 50 || height < 30) return null;
  return (
    <g>
      <rect x={x} y={y} width={width} height={height} rx={4}
        style={{ fill: CHART_COLORS[Math.abs(name?.charCodeAt(0) || 0) % CHART_COLORS.length], fillOpacity: 0.85, stroke: '#0a0f1c', strokeWidth: 2 }} />
      {width > 70 && height > 40 && (
        <>
          <text x={x + 8} y={y + 18} fill="#fff" fontSize={11} fontWeight={600}>
            {name?.replace(/_/g, ' ').slice(0, Math.floor(width / 7))}
          </text>
          <text x={x + 8} y={y + 34} fill="rgba(255,255,255,0.7)" fontSize={10}>{count} calls</text>
        </>
      )}
    </g>
  );
};

export default function RootCause({ client }) {
  const { data, loading } = useApi(buildQuery('/api/analytics/root-causes', { client }), [client]);

  if (loading || !data) return <div className="page-header"><h1>Loading...</h1></div>;

  const treemapData = data.distribution.map(d => ({ name: d.category, count: d.count, size: d.count }));
  const allCats = data.distribution.map(d => d.category);

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1>Root Cause Analysis</h1>
        <p>AI-detected root cause patterns and recurring issue identification {client !== 'All' ? `• ${client}` : ''}</p>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header"><span className="card-title">Root Cause Treemap</span></div>
          <ResponsiveContainer width="100%" height={300}>
            <Treemap data={treemapData} dataKey="size" aspectRatio={4/3}
              content={<TreemapContent />} />
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="card-header"><span className="card-title">Distribution</span></div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data.distribution} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis type="number" tick={{ fill: '#8b95a8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="category" tick={{ fill: '#8b95a8', fontSize: 10 }} width={110}
                     axisLine={false} tickLine={false} tickFormatter={v => v.replace(/_/g, ' ')} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="count" fill="#00d4aa" radius={[0, 6, 6, 0]} name="Calls">
                {data.distribution.map((_, i) => (
                  <rect key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header"><span className="card-title">Root Cause Trends Over Time</span></div>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={data.trends}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="month" tick={{ fill: '#8b95a8', fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: '#8b95a8', fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: 11 }} formatter={v => v.replace(/_/g, ' ')} />
            {allCats.map((cat, i) => (
              <Area key={cat} type="monotone" dataKey={cat} stackId="1" stroke={CHART_COLORS[i % CHART_COLORS.length]}
                    fill={CHART_COLORS[i % CHART_COLORS.length]} fillOpacity={0.4} name={cat.replace(/_/g, ' ')} />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="card">
        <div className="card-header"><span className="card-title">Top Recurring Issues</span></div>
        <table className="data-table">
          <thead><tr><th>#</th><th>Issue</th><th>Occurrences</th><th>Recurrence Score</th><th>Priority</th></tr></thead>
          <tbody>
            {data.top_recurring?.map((r, i) => (
              <tr key={i}>
                <td>{i + 1}</td>
                <td style={{ color: 'var(--text-primary)', maxWidth: 400 }}>{r.cause}</td>
                <td><span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{r.count}</span></td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div className="progress-bar" style={{ width: 80 }}>
                      <div className="progress-bar-fill" style={{ width: `${r.recurrence_score * 100}%`,
                           background: r.recurrence_score > 0.7 ? 'var(--accent-red)' : r.recurrence_score > 0.4 ? 'var(--accent-amber)' : 'var(--accent-green)' }} />
                    </div>
                    <span>{r.recurrence_score}</span>
                  </div>
                </td>
                <td><span className={`badge ${r.recurrence_score > 0.7 ? 'red' : r.recurrence_score > 0.4 ? 'amber' : 'green'}`}>
                  {r.recurrence_score > 0.7 ? 'High' : r.recurrence_score > 0.4 ? 'Medium' : 'Low'}
                </span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
