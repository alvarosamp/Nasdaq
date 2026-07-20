import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import { usePolling } from '../hooks/usePolling';
import type { DashboardSummary, EarningsEvent, EconomicEvent } from '../types';

function fmtTime(iso: string | null) {
  if (!iso) return 'sem dados';
  return new Date(iso).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) + ' UTC';
}

export function Dashboard() {
  const { data, lastUpdated } = usePolling<DashboardSummary>('/api/dashboard-summary', 20000);
  const [econ, setEcon] = useState<EconomicEvent[]>([]);
  const [earnings, setEarnings] = useState<EarningsEvent[]>([]);

  useEffect(() => {
    api.get<EconomicEvent[]>('/api/economic-events?days_ahead=7&limit=10').then(setEcon).catch(() => {});
    api.get<EarningsEvent[]>('/api/earnings-events?days_ahead=7&limit=10').then(setEarnings).catch(() => {});
  }, []);

  const rows = data?.rows ?? [];
  const alerts = data?.alerts ?? [];

  return (
    <div className="container">
      {(econ.length > 0 || earnings.length > 0) && (
        <section className="events-card">
          <h2>
            Próximos eventos (7 dias) — <Link to="/mercado">ver painel completo</Link>
          </h2>
          <ul className="alert-list">
            {econ.map((e, i) => (
              <li key={`econ-${i}`}>
                🌎 {new Date(e.event_date).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })} —{' '}
                {e.event_name} ({e.country}) <span className="muted">impacto: {e.impact}</span>
              </li>
            ))}
            {earnings.map((e, i) => (
              <li key={`earn-${i}`}>
                📅 {new Date(e.event_date).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })} — earnings de{' '}
                <strong>{e.symbol}</strong>
              </li>
            ))}
          </ul>
        </section>
      )}

      <h1>
        Watchlist{' '}
        {lastUpdated && <span className="muted">(atualizado {lastUpdated.toLocaleTimeString('pt-BR')})</span>}
      </h1>
      <div className="table-scroll">
        <table className="table">
          <thead>
            <tr>
              <th>Símbolo</th>
              <th>Preço</th>
              <th>Variação</th>
              <th>Atualizado</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={5} className="muted">
                  Watchlist vazia. Adicione ativos em "Watchlist &amp; Regras".
                </td>
              </tr>
            ) : (
              rows.map((r) => (
                <tr key={r.id}>
                  <td>
                    <Link to={`/ativo/${r.symbol}`}>{r.symbol}</Link>{' '}
                    {r.label && <span className="muted">({r.label})</span>}
                  </td>
                  {r.price !== null ? (
                    <>
                      <td>{r.price.toFixed(2)}</td>
                      <td className={(r.change_pct ?? 0) >= 0 ? 'up' : 'down'}>{(r.change_pct ?? 0).toFixed(2)}%</td>
                      <td className="muted">{fmtTime(r.taken_at)}</td>
                    </>
                  ) : (
                    <td colSpan={3} className="muted">
                      sem dados ainda
                    </td>
                  )}
                  <td>
                    <Link to={`/ativo/${r.symbol}`}>ver gráfico →</Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <h2>Alertas recentes</h2>
      <ul className="alert-list">
        {alerts.length === 0 ? (
          <li className="muted">Nenhum alerta disparado ainda.</li>
        ) : (
          alerts.map((a, i) => (
            <li key={i}>
              <span className="muted">{fmtTime(a.triggered_at)}</span> — <strong>{a.symbol}</strong> {a.message}
              {a.delivered_telegram && <span className="tag">Telegram ✓</span>}
            </li>
          ))
        )}
      </ul>
    </div>
  );
}
