export function formatNumber(n) {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
  return n?.toString() || '0';
}

export function formatPercent(n, decimals = 1) {
  return (n * 100).toFixed(decimals) + '%';
}

export function formatDuration(seconds) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}m ${s}s`;
}

export function sentimentColor(score) {
  if (score > 0.3) return 'var(--accent-green)';
  if (score > -0.3) return 'var(--accent-amber)';
  return 'var(--accent-red)';
}

export function csatColor(score) {
  if (score >= 4) return 'var(--accent-green)';
  if (score >= 3) return 'var(--accent-amber)';
  return 'var(--accent-red)';
}

export function toneEmoji(tone) {
  const map = { satisfied: '😊', neutral: '😐', frustrated: '😤', angry: '😡', very_angry: '🤬', concerned: '😟', relieved: '😌' };
  return map[tone] || '📊';
}

export const CHART_COLORS = ['#00d4aa', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444', '#06b6d4', '#ec4899'];
