import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { OperationalHealth } from '../types';

function fmt(iso: string | null) {
  return iso ? new Date(iso).toLocaleString('pt-BR') : '-';
}

export function Operacoes() {
  const [health, setHealth] = useState<OperationalHealth | null>(null);

  useEffect(() => {
    api.get<OperationalHealth>('/api/operations/health').then(setHealth).catch(() => {});
  }, []);

  if (!health) {
    return (
      <div className="container">
        <h1>Operações</h1>
        <p className="muted">Carregando saúde operacional...</p>
      </div>
    );
  }

  return (
    <div className="container dashboard-container">
      <div className="page-header">
        <div>
          <p className="eyebrow">Auditoria operacional</p>
          <h1>Operações</h1>
          <p className="muted">Fontes, jobs, qualidade de dados, alertas e trilha de auditoria.</p>
        </div>
        <span className="status-pill good">{health.status}</span>
      </div>

      <section className="metric-grid">
        <div className="metric-card"><span className="metric-label">Último snapshot</span><strong>{fmt(health.latest_snapshot_at)}</strong></div>
        <div className="metric-card"><span className="metric-label">Idade</span><strong>{health.snapshot_age_minutes ?? '-'} min</strong></div>
        <div className="metric-card"><span className="metric-label">Alta confiança</span><strong>{health.data_quality.HIGH}</strong></div>
        <div className="metric-card"><span className="metric-label">Atenção/Baixa</span><strong>{health.data_quality.MEDIUM + health.data_quality.LOW}</strong></div>
      </section>

      <section className="dashboard-grid">
        <div className="panel">
          <h2>Fontes</h2>
          <ul className="source-list">
            {Object.entries(health.providers).map(([key, value]) => (
              <li key={key}><strong>{key}</strong><span>{value ? 'configurada' : 'indisponível'}</span></li>
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
