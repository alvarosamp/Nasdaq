import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { TraderProfile, TraderProfileGroup } from '../types';

function fmtMoney(value: number) {
  return value.toLocaleString('pt-BR', { style: 'currency', currency: 'USD' });
}

function fmtDate(iso: string) {
  return new Date(iso).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
}

function GroupTable({ rows, empty }: { rows: TraderProfileGroup[]; empty: string }) {
  return (
    <div className="table-scroll compact-scroll">
      <table className="table dense-table">
        <thead>
          <tr>
            <th>Grupo</th>
            <th>Trades</th>
            <th>P&amp;L</th>
            <th>Acerto</th>
            <th>Ret. medio</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={5} className="muted">
                {empty}
              </td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr key={row.key}>
                <td>{row.key}</td>
                <td>{row.trades}</td>
                <td className={row.pnl >= 0 ? 'up' : 'down'}>{fmtMoney(row.pnl)}</td>
                <td>{row.win_rate.toFixed(1)}%</td>
                <td className={row.avg_return_pct >= 0 ? 'up' : 'down'}>{row.avg_return_pct.toFixed(2)}%</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

export function Perfil() {
  const [profile, setProfile] = useState<TraderProfile | null>(null);

  useEffect(() => {
    api.get<TraderProfile>('/api/profile/trader').then(setProfile).catch(() => {});
  }, []);

  if (!profile) {
    return (
      <div className="container">
        <h1>Perfil do Trader</h1>
        <p className="muted">Carregando diario inteligente...</p>
      </div>
    );
  }

  const s = profile.summary;

  return (
    <div className="container dashboard-container">
      <div className="page-header">
        <div>
          <p className="eyebrow">Diario inteligente</p>
          <h1>Perfil do Trader</h1>
          <p className="muted">
            O sistema analisa suas operacoes fechadas para encontrar padroes, pontos fortes e erros recorrentes.
          </p>
        </div>
      </div>

      <section className="metric-grid">
        <div className="metric-card">
          <span className="metric-label">P&amp;L fechado</span>
          <strong className={s.total_pnl >= 0 ? 'up' : 'down'}>{fmtMoney(s.total_pnl)}</strong>
          <span className="muted">{s.closed_trades} trade(s) fechado(s)</span>
        </div>
        <div className="metric-card">
          <span className="metric-label">Taxa de acerto</span>
          <strong>{s.win_rate.toFixed(1)}%</strong>
          <span className="muted">{s.transactions} transacao(oes)</span>
        </div>
        <div className="metric-card">
          <span className="metric-label">Expectativa</span>
          <strong className={s.expectancy >= 0 ? 'up' : 'down'}>{fmtMoney(s.expectancy)}</strong>
          <span className="muted">media estimada por trade</span>
        </div>
        <div className="metric-card">
          <span className="metric-label">Profit factor</span>
          <strong>{s.profit_factor === 999 ? 'sem perdas' : s.profit_factor.toFixed(2)}</strong>
          <span className="muted">{s.avg_holding_hours.toFixed(1)}h medio em posicao</span>
        </div>
      </section>

      <section className="dashboard-grid">
        <div className="panel">
          <h2>Diagnostico</h2>
          <ul className="decision-list">
            {profile.insights.length === 0 ? (
              <li className="muted">Ainda nao ha dados suficientes para insights confiaveis.</li>
            ) : (
              profile.insights.map((item) => <li key={item}>{item}</li>)
            )}
          </ul>
        </div>
        <div className="panel">
          <h2>Resumo operacional</h2>
          <ul className="source-list">
            <li>
              <strong>Ganho medio</strong>
              <span>{fmtMoney(s.avg_win)}</span>
            </li>
            <li>
              <strong>Perda media</strong>
              <span>{fmtMoney(s.avg_loss)}</span>
            </li>
            <li>
              <strong>Simbolos com posicao/historico</strong>
              <span>{s.open_symbols.length ? s.open_symbols.join(', ') : 'nenhum'}</span>
            </li>
          </ul>
        </div>
      </section>

      <section className="dashboard-grid">
        <div className="panel">
          <h2>Por ativo</h2>
          <GroupTable rows={profile.by_symbol} empty="Nenhum trade fechado por ativo ainda." />
        </div>
        <div className="panel">
          <h2>Por horario de entrada</h2>
          <GroupTable rows={profile.by_hour} empty="Nenhum horario analisavel ainda." />
        </div>
      </section>

      <section className="panel">
        <h2>Por estilo</h2>
        <GroupTable rows={profile.by_style} empty="Nenhum estilo detectado ainda." />
      </section>

      <section className="panel">
        <h2>Diario inteligente</h2>
        <div className="table-scroll">
          <table className="table dense-table">
            <thead>
              <tr>
                <th>Ativo</th>
                <th>Entrada</th>
                <th>Saida</th>
                <th>P&amp;L</th>
                <th>Retorno</th>
                <th>Licao</th>
              </tr>
            </thead>
            <tbody>
              {profile.journal.length === 0 ? (
                <tr>
                  <td colSpan={6} className="muted">
                    Feche operacoes em Posicoes para gerar diario inteligente.
                  </td>
                </tr>
              ) : (
                profile.journal.map((entry) => (
                  <tr key={`${entry.symbol}-${entry.entry_at}-${entry.exit_at}`}>
                    <td>{entry.symbol}</td>
                    <td>{fmtDate(entry.entry_at)}</td>
                    <td>{fmtDate(entry.exit_at)}</td>
                    <td className={entry.pnl >= 0 ? 'up' : 'down'}>{fmtMoney(entry.pnl)}</td>
                    <td className={entry.return_pct >= 0 ? 'up' : 'down'}>{entry.return_pct.toFixed(2)}%</td>
                    <td className="muted">{entry.lesson}</td>
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
