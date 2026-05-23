import { useState, useEffect, useCallback } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const WS_BASE = import.meta.env.VITE_WS_BASE_URL || (API_BASE.startsWith('https') ? API_BASE.replace('https://', 'wss://') : API_BASE.replace('http://', 'ws://'));

// Global WebSocket singleton
let ws = null;
const wsListeners = new Set();
export let isLive = false;

function initWebSocket() {
  if (ws) return;
  ws = new WebSocket(`${WS_BASE}/ws/updates`);
  
  ws.onopen = () => {
    isLive = true;
    window.dispatchEvent(new Event('liveStatusChange'));
  };
  
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.type === 'NEW_CALLS') {
        wsListeners.forEach(fn => fn());
      }
    } catch (e) {}
  };

  ws.onclose = () => {
    ws = null;
    isLive = false;
    window.dispatchEvent(new Event('liveStatusChange'));
    setTimeout(initWebSocket, 3000);
  };
}

export function useApi(endpoint, deps = []) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async (isSilentUpdate = false) => {
    if (!endpoint) return;
    if (!isSilentUpdate) setLoading(true);
    try {
      const res = await fetch(`${API_BASE}${endpoint}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setData(json);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [endpoint]);

  useEffect(() => { 
    fetchData(); 
    
    // Initialize WS and listen for updates
    initWebSocket();
    const handleUpdate = () => fetchData(true); // Silent refetch
    wsListeners.add(handleUpdate);
    
    return () => wsListeners.delete(handleUpdate);
  }, [fetchData, ...deps]);

  return { data, loading, error, refetch: fetchData };
}

export function useApiPost(endpoint) {
  const [loading, setLoading] = useState(false);

  const post = async (body) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const json = await res.json();
      setLoading(false);
      return json;
    } catch (err) {
      setLoading(false);
      throw err;
    }
  };

  return { post, loading };
}

export function buildQuery(base, params) {
  const query = Object.entries(params)
    .filter(([_, v]) => v && v !== 'All')
    .map(([k, v]) => `${k}=${encodeURIComponent(v)}`)
    .join('&');
  return query ? `${base}?${query}` : base;
}
