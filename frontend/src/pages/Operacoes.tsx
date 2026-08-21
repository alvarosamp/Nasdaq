import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { OperationalHealth } from '../types';

function fmt(iso: string | null) {
  return iso ? new Date(iso).toLocaleString('pt-BR') : '-';
}

function pct(value: number | null) {
  return value === null ? '-' : `${(value * 100).toFixed(2)}%`;
}

function money(value: number | null) {
  return value === null
    ? '-'
    : `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export function Operacoes() {
  const [health, setHealth] = useState<OperationalHealth | null>(null);

  useEffect(() => {
    api.get<OperationalHealth>('/api/operations/health').then(setHealth).catch(() => {});
  }, []);

  if (!health) {
    return (
      <div className="container">
        <h1>Operacoes</h1>
        <p className="muted">Carregando diagnostico operacional...</p>
      </div>
    );
  }

  return (
    <div className="container dashboard-container">
      <div className="page-header">
        <div>
          <p className="eyebrow">Auditoria operacional</p>
          <h1>Operacoes</h1>
          <p className="muted">Diagnostico unico: dados, cache, modelo, paper trading, jobs e prontidao.</p>
        </div>
        <span className={`status-pill ${health.status === 'ok' ? 'good' : 'warn'}`}>{health.status}</span>
      </div>

      <section className="metric-grid">
        <div className="metric-card">
          <span className="metric-label">Carteira paper</span>
          <strong>{money(health.paper_simulator.portfolio_value)}</strong>
        </div>
        <div className="metric-card">
          <span className="metric-label">Cache OHLCV</span>
          <strong>{health.market_cache.ready ? 'OK' : 'Atencao'}</strong>
        </div>
        <div className="metric-card">
          <span className="metric-label">Modelo</span>
          <strong>{health.probability_model.status}</strong>
        </div>
        <div className="metric-card">
          <span className="metric-label">Automacao</span>
          <strong>{health.automation.verdict}</strong>
        </div>
      </section>

      <section className="dashboard-grid">
        <div className="panel">
          <h2>Prontidao</h2>
          <p className="muted">{health.readiness.recommendation}</p>
          <ul className="source-list">
            <li><strong>Nivel</strong><span>{health.readiness.level}</span></li>
            <li><strong>Trade automatico</strong><span>{health.readiness.trade_automation_allowed ? 'liberado' : 'bloqueado'}</span></li>
            <li><strong>Bloqueios</strong><span>{health.readiness.blockers.length ? health.readiness.blockers.join(', ') : 'nenhum'}</span></li>
          </ul>
        </div>
        <div className="panel">
          <h2>Paper trading</h2>
          <ul className="source-list">
            <li><strong>Capital inicial</strong><span>{money(health.paper_simulator.initial_capital)}</span></li>
            <li><strong>Caixa</strong><span>{money(health.paper_simulator.cash)}</span></li>
            <li><strong>Posicoes abertas</strong><span>{health.paper_simulator.open_positions}</span></li>
            <li><strong>Trades fechados</strong><span>{health.paper_simulator.closed_trades}</span></li>
          </ul>
        </div>
      </section>

      <section className="dashboard-grid">
        <div className="panel">
          <h2>Cache de mercado</h2>
          <ul className="source-list">
            {health.market_cache.rows.map((row) => (
              <li key={row.symbol}>
                <strong>{row.symbol}</strong>
                <span>{row.rows} candles | close {row.last_close ?? '-'}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="panel">
          <h2>Modelo de probabilidade</h2>
          <p className="muted">{health.probability_model.recommendation}</p>
          <ul className="source-list">
            <li><strong>Amostras treino</strong><span>{health.probability_model.train_samples ?? '-'}</span></li>
            <li><strong>Holdout</strong><span>{pct(health.probability_model.holdout_accuracy)}</span></li>
            <li><strong>Baseline</strong><span>{pct(health.probability_model.holdout_baseline_accuracy)}</span></li>
          </ul>
        </div>
      </section>

      <section className="dashboard-grid">
        <div className="panel">
          <h2>Banco</h2>
          <ul className="source-list">
            {Object.entries(health.db.counts).map(([key, value]) => (
              <li key={key}><strong>{key}</strong><span>{value}</span></li>
            ))}
          </ul>
        </div>
        <div className="panel">
          <h2>Qualidade</h2>
          <ul className="source-list">
            <li><strong>Alta</strong><span>{health.data_quality.HIGH}</span></li>
            <li><strong>Media</strong><span>{health.data_quality.MEDIUM}</span></li>
            <li><strong>Baixa</strong><span>{health.data_quality.LOW}</span></li>
            <li><strong>Ultimo snapshot</strong><span>{fmt(health.latest_snapshot_at)}</span></li>
          </ul>
        </div>
      </section>

      <section className="dashboard-grid">
        <div className="panel">
          <h2>Fontes</h2>
          <ul className="source-list">
            {Object.entries(health.providers).map(([key, value]) => (
              <li key={key}><strong>{key}</strong><span>{value ? 'configurada' : 'indisponivel'}</span></li>
            ))}
          </ul>
        </div>
        <div className="panel">
          <h2>Jobs</h2>
          <ul className="source-list">
            {Object.entries(health.jobs).map(([key, value]) => (
              <li key={key}><strong>{key}</strong><span>{String(value)}</span></li>
            ))}
          </ul>
        </div>
      </section>

      <section className="dashboard-grid">
        <div className="panel">
          <h2>Alertas recentes</h2>
          <ul className="source-list">
            {health.recent_alerts.map((alert) => (
              <li key={`${alert.symbol}-${alert.triggered_at}`}><strong>{alert.symbol}</strong><span>{alert.message}</span></li>
            ))}
          </ul>
        </div>
        <div className="panel">
          <h2>Auditoria</h2>
          <ul className="source-list">
            {health.recent_audit_logs.map((log) => (
              <li key={`${log.action}-${log.created_at}`}><strong>{log.action}</strong><span>{log.entity_type} {log.entity_id}</span></li>
            ))}
          </ul>
        </div>
      </section>
    </div>
  );
}
