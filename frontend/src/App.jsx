import { BrowserRouter, Routes, Route, NavLink, useSearchParams } from 'react-router-dom';
import { useState, useEffect } from 'react';
import {
  LayoutDashboard, Search, AlertTriangle, SmilePlus,
  Users, List, MessageSquare, Brain
} from 'lucide-react';
import Dashboard from './pages/Dashboard';
import RootCause from './pages/RootCause';
import Escalations from './pages/Escalations';
import Sentiment from './pages/Sentiment';
import AgentPerformance from './pages/AgentPerformance';
import CallExplorer from './pages/CallExplorer';
import AIChat from './pages/AIChat';
import { useApi, isLive } from './hooks/useApi';
import './App.css';

const NAV_ITEMS = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/root-cause', icon: Search, label: 'Root Cause Analysis' },
  { path: '/escalations', icon: AlertTriangle, label: 'Escalation Analytics' },
  { path: '/sentiment', icon: SmilePlus, label: 'Sentiment Analysis' },
  { path: '/agents', icon: Users, label: 'Agent Performance' },
  { path: '/calls', icon: List, label: 'Call Explorer' },
  { path: '/chat', icon: MessageSquare, label: 'AI Chat' },
];

function AppContent() {
  const [client, setClient] = useState('All');
  const { data: clients } = useApi('/api/clients');
  const [live, setLive] = useState(isLive);

  useEffect(() => {
    const handleStatus = () => setLive(isLive);
    window.addEventListener('liveStatusChange', handleStatus);
    return () => window.removeEventListener('liveStatusChange', handleStatus);
  }, []);

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-logo" style={{ position: 'relative' }}>
          <div className="logo-icon"><Brain size={20} color="#fff" /></div>
          <div className="logo-text">Customer<br/><span>Interaction Insights</span></div>
          {live && (
            <div style={{ position: 'absolute', top: 12, right: 12, display: 'flex', alignItems: 'center', gap: 6, fontSize: 10, color: '#00d4aa', fontWeight: 700, background: 'rgba(0, 212, 170, 0.1)', padding: '4px 8px', borderRadius: 12, border: '1px solid rgba(0, 212, 170, 0.2)' }}>
              <span style={{ width: 6, height: 6, background: '#00d4aa', borderRadius: '50%', boxShadow: '0 0 8px #00d4aa' }}></span> LIVE
            </div>
          )}
        </div>
        <nav className="sidebar-nav">
          {NAV_ITEMS.map(item => (
            <NavLink
              key={item.path}
              to={`${item.path}${client !== 'All' ? `?client=${encodeURIComponent(client)}` : ''}`}
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
              end={item.path === '/'}
            >
              <item.icon size={18} />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <label className="client-label">Filter by Client</label>
          <select
            className="client-selector"
            value={client}
            onChange={e => setClient(e.target.value)}
          >
            <option value="All">All Clients</option>
            {(clients || []).map(c => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>
      </aside>
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Dashboard client={client} />} />
          <Route path="/root-cause" element={<RootCause client={client} />} />
          <Route path="/escalations" element={<Escalations client={client} />} />
          <Route path="/sentiment" element={<Sentiment client={client} />} />
          <Route path="/agents" element={<AgentPerformance client={client} />} />
          <Route path="/calls" element={<CallExplorer client={client} />} />
          <Route path="/chat" element={<AIChat client={client} />} />
        </Routes>
      </main>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}

export default App;
