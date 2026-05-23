import { useState, useRef, useEffect } from 'react';
import { useApiPost } from '../hooks/useApi';
import { Send, Bot, User, Sparkles } from 'lucide-react';

const SUGGESTIONS = [
  "What are the top root causes for Verizon?",
  "Show me escalation analytics for Wells Fargo",
  "Which agents need coaching?",
  "What's driving customer frustration at Comcast?",
  "Give me an overview of all clients",
  "How is our CSAT score trending?",
];

function formatMessage(text) {
  if (!text) return '';
  // Bold
  let html = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  // Italic
  html = html.replace(/_(.*?)_/g, '<em>$1</em>');
  // Table (simple markdown tables)
  if (html.includes('|')) {
    const lines = html.split('\n');
    let inTable = false;
    let tableHtml = '<table class="data-table" style="margin: 8px 0">';
    const result = [];
    for (const line of lines) {
      if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
        if (line.includes('---')) continue;
        const cells = line.split('|').filter(c => c.trim());
        if (!inTable) {
          tableHtml += '<thead><tr>' + cells.map(c => `<th>${c.trim()}</th>`).join('') + '</tr></thead><tbody>';
          inTable = true;
        } else {
          tableHtml += '<tr>' + cells.map(c => `<td>${c.trim()}</td>`).join('') + '</tr>';
        }
      } else {
        if (inTable) {
          tableHtml += '</tbody></table>';
          result.push(tableHtml);
          tableHtml = '<table class="data-table" style="margin: 8px 0">';
          inTable = false;
        }
        result.push(line);
      }
    }
    if (inTable) {
      tableHtml += '</tbody></table>';
      result.push(tableHtml);
    }
    html = result.join('\n');
  }
  // Line breaks
  html = html.replace(/\n/g, '<br/>');
  return html;
}

export default function AIChat({ client }) {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: '👋 Hi! I\'m your **AI Analytics Assistant** powered by advanced NLP. Ask me anything about your call center data — root causes, escalation patterns, agent performance, sentiment trends, and more.\n\nTry one of the suggestions below or type your own question!' }
  ]);
  const [input, setInput] = useState('');
  const { post, loading } = useApiPost('/api/chat');
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (text) => {
    const msg = text || input.trim();
    if (!msg || loading) return;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: msg }]);

    try {
      const res = await post({ message: msg, client: client !== 'All' ? client : null });
      setMessages(prev => [...prev, { role: 'assistant', content: res.response }]);
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: '❌ Sorry, something went wrong. Please try again.' }]);
    }
  };

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Sparkles size={24} style={{ color: 'var(--accent-teal)' }} /> AI Analytics Chat
        </h1>
        <p>Ask natural language questions about your call center data — powered by RAG pipeline {client !== 'All' ? `• Filtered: ${client}` : ''}</p>
      </div>

      <div className="card chat-container">
        <div className="chat-messages">
          {messages.map((msg, i) => (
            <div key={i} className={`chat-msg ${msg.role}`}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8, fontSize: 11, fontWeight: 600, opacity: 0.7 }}>
                {msg.role === 'assistant' ? <Bot size={14} /> : <User size={14} />}
                {msg.role === 'assistant' ? 'AI Assistant' : 'You'}
              </div>
              <div dangerouslySetInnerHTML={{ __html: formatMessage(msg.content) }} />
            </div>
          ))}
          {loading && (
            <div className="chat-msg assistant">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div className="loading-skeleton" style={{ width: 8, height: 8, borderRadius: '50%' }} />
                <div className="loading-skeleton" style={{ width: 8, height: 8, borderRadius: '50%', animationDelay: '0.2s' }} />
                <div className="loading-skeleton" style={{ width: 8, height: 8, borderRadius: '50%', animationDelay: '0.4s' }} />
                <span style={{ marginLeft: 8, fontSize: 12, color: 'var(--text-muted)' }}>Analyzing data...</span>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {messages.length <= 1 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, padding: '12px 0' }}>
            {SUGGESTIONS.map((s, i) => (
              <button key={i} onClick={() => sendMessage(s)}
                style={{ padding: '8px 14px', borderRadius: 20, background: 'rgba(0,212,170,0.08)', border: '1px solid rgba(0,212,170,0.2)',
                         color: 'var(--accent-teal)', fontSize: 12, fontWeight: 500, cursor: 'pointer', transition: 'all 0.2s' }}>
                {s}
              </button>
            ))}
          </div>
        )}

        <div className="chat-input-area">
          <input className="chat-input" value={input} onChange={e => setInput(e.target.value)}
                 onKeyDown={e => e.key === 'Enter' && sendMessage()}
                 placeholder="Ask about root causes, escalations, sentiment, agents..."
                 disabled={loading} />
          <button className="chat-send-btn" onClick={() => sendMessage()} disabled={!input.trim() || loading}>
            <Send size={16} /> Send
          </button>
        </div>
      </div>
    </div>
  );
}
