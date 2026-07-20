import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { usePolling } from '../hooks/usePolling';
import type { EarningsEvent, EconomicEvent, NewsItem } from '../types';

function fmtDateTime(iso: string) {
  return new Date(iso).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) + ' UTC';
}

export function Mercado() {
  const { data: news, lastUpdated } = usePolling<NewsItem[]>('/api/news?limit=40', 60000);
  const [econ, setEcon] = useState<EconomicEvent[]>([]);
  const [earnings, setEarnings] = useState<EarningsEvent[]>([]);

  useEffect(() => {
    api.get<EconomicEvent[]>('/api/economic-events?days_ahead=14&limit=50').then(setEcon).catch(() => {});
    api.get<EarningsEvent[]>('/api/earnings-events?days_ahead=14&limit=50').then(setEarnings).catch(() => {});
  }, []);

  return (
    <div className="container">
      <h1>Painel de Mercado</h1>

      <section>
        <h2>
          Notícias recentes{' '}
          {lastUpdated && <span className="muted">(atualizado {lastUpdated.toLocaleTimeString('pt-BR')})</span>}
        </h2>
        <ul className="alert-list">
          {!news || news.length === 0 ? (
            <li className="muted">Nenhuma notícia coletada ainda.</li>
          ) : (
            news.map((n, i) => (
              <li key={i}>
                <span className="muted">{fmtDateTime(n.published_at)}</span> — <strong>{n.symbol}</strong>{' '}
                <a href={n.url} target="_blank" rel="noopener noreferrer">
                  {n.headline}
                </a>{' '}
                {n.source && <span className="muted">({n.source})</span>}
              </li>
            ))
          )}
        </ul>
      </section>

      <section>
        <h2>Calendário econômico (próximos dias)</h2>
        <div className="table-scroll">
          <table className="table">
            <thead>
              <tr>
                <th>Data</th>
                <th>Evento</th>
                <th>País</th>
                <th>Impacto</th>
                <th>Prev.</th>
                <th>Ant.</th>
              </tr>
            </thead>
            <tbody>
              {econ.length === 0 ? (
                <tr>
                  <td colSpan={6} className="muted">
                    Nenhum evento econômico carregado ainda.
                  </td>
                </tr>
              ) : (
                econ.map((e, i) => (
                  <tr key={i}>
                    <td>{fmtDateTime(e.event_date)}</td>
                    <td>{e.event_name}</td>
                    <td>{e.country}</td>
                    <td className={e.impact === 'high' ? 'down' : ''}>{e.impact}</td>
                    <td>{e.forecast}</td>
                    <td>{e.previous}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h2>Earnings da watchlist</h2>
        <div className="table-scroll">
          <table className="table">
            <thead>
              <tr>
                <th>Data</th>
                <th>Símbolo</th>
                <th>EPS estimado</th>
                <th>Receita estimada</th>
              </tr>
            </thead>
            <tbody>
              {earnings.length === 0 ? (
                <tr>
                  <td colSpan={4} className="muted">
                    Nenhum earnings carregado ainda.
                  </td>
                </tr>
              ) : (
                earnings.map((e, i) => (
                  <tr key={i}>
                    <td>{new Date(e.event_date).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })}</td>
                    <td>{e.symbol}</td>
                    <td>{e.eps_estimate ?? '-'}</td>
                    <td>{e.revenue_estimate !== null ? e.revenue_estimate.toLocaleString('pt-BR') : '-'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
