import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { RULE_META } from '../hooks/useRuleConditions';
import type { AlertLog, WatchlistItem } from '../types';

function fmtTime(iso: string) {
  return new Date(iso).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) + ' UTC';
}

export function Alertas() {
  const [symbols, setSymbols] = useState<string[]>([]);
  const [alerts, setAlerts] = useState<AlertLog[]>([]);
  const [symbolFilter, setSymbolFilter] = useState('');
  const [ruleTypeFilter, setRuleTypeFilter] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<WatchlistItem[]>('/api/watchlist')
      .then((items) => setSymbols(items.map((i) => i.symbol).sort()))
      .catch(() => {});
  }, []);

  async function loadAlerts() {
    setLoading(true);
    const params = new URLSearchParams({ limit: '100' });
    if (symbolFilter) params.set('symbol', symbolFilter);
    if (ruleTypeFilter) params.set('rule_type', ruleTypeFilter);
    try {
      setAlerts(await api.get<AlertLog[]>(`/api/alerts?${params.toString()}`));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAlerts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbolFilter, ruleTypeFilter]);

  return (
    <div className="container">
      <h1>Alertas</h1>

      <div className="filters">
        <select value={symbolFilter} onChange={(e) => setSymbolFilter(e.target.value)}>
          <option value="">Todos os símbolos</option>
          {symbols.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <select value={ruleTypeFilter} onChange={(e) => setRuleTypeFilter(e.target.value)}>
          <option value="">Todos os tipos</option>
          {Object.keys(RULE_META).map((rt) => (
            <option key={rt} value={rt}>
              {rt}
            </option>
          ))}
        </select>
      </div>

      <ul className="alert-list">
        {loading ? (
          <li className="muted">Carregando...</li>
        ) : alerts.length === 0 ? (
          <li className="muted">Nenhum alerta encontrado com esse filtro.</li>
        ) : (
          alerts.map((a) => (
            <li key={a.id}>
              <span className="muted">{fmtTime(a.triggered_at)}</span> — <strong>{a.symbol}</strong>{' '}
              <span className="muted">[{a.rule_type}]</span> {a.message}
              {a.delivered_telegram && <span className="tag">Telegram ✓</span>}
            </li>
          ))
        )}
      </ul>
    </div>
  );
}
