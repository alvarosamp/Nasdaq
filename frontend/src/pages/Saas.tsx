import { useEffect, useState, type FormEvent } from 'react';
import { api } from '../api/client';
import { useToast } from '../context/ToastContext';
import type { NotificationChannelType, SaasOverview, SubscriptionPlan } from '../types';

const planLabels: Record<SubscriptionPlan, string> = {
  FREE: 'Free',
  PRO: 'Pro',
  ADVISOR: 'Advisor',
};

const usageLabels: Record<string, string> = {
  watchlist_items: 'Ativos',
  alert_rules: 'Regras',
  notification_channels: 'Canais',
  report_templates: 'Templates',
  client_segments: 'Segmentos',
  ai_questions_per_month: 'Perguntas IA',
};

function pct(used: number, limit: number) {
  if (limit <= 0) return 100;
  return Math.min(100, Math.round((used / limit) * 100));
}

export function Saas() {
  const toast = useToast();
  const [overview, setOverview] = useState<SaasOverview | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    try {
      setOverview(await api.get<SaasOverview>('/api/saas/overview'));
    } catch {
      toast('Erro ao carregar configurações SaaS', 'error');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function changePlan(plan: SubscriptionPlan) {
    try {
      setOverview(await api.put<SaasOverview>('/api/saas/plan', { plan }));
      toast(`Plano alterado para ${planLabels[plan]}`, 'success');
    } catch {
      toast('Erro ao alterar plano', 'error');
    }
  }

  async function saveWorkspace(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    try {
      await api.put('/api/saas/workspace', {
        name: form.get('name'),
        brand_name: form.get('brand_name'),
      });
      toast('Workspace atualizado', 'success');
      load();
    } catch {
      toast('Erro ao salvar workspace', 'error');
    }
  }

  async function addChannel(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    try {
      await api.post('/api/saas/channels', {
        channel_type: form.get('channel_type') as NotificationChannelType,
        destination: form.get('destination'),
      });
      e.currentTarget.reset();
      toast('Canal adicionado', 'success');
      load();
    } catch (err) {
      toast(err instanceof Error ? err.message : 'Erro ao criar canal', 'error');
    }
  }

  async function addTemplate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    try {
      await api.post('/api/saas/report-templates', {
        title: form.get('title'),
        audience: form.get('audience'),
        include_ai_summary: form.get('include_ai_summary') === 'on',
        include_backtest: form.get('include_backtest') === 'on',
      });
      e.currentTarget.reset();
      toast('Template criado', 'success');
      load();
    } catch (err) {
      toast(err instanceof Error ? err.message : 'Erro ao criar template', 'error');
    }
  }

  async function addSegment(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    try {
      await api.post('/api/saas/segments', {
        name: form.get('name'),
        description: form.get('description'),
      });
      e.currentTarget.reset();
      toast('Segmento criado', 'success');
      load();
    } catch (err) {
      toast(err instanceof Error ? err.message : 'Erro ao criar segmento', 'error');
    }
  }

  if (loading || !overview) {
    return (
      <div className="container">
        <h1>SaaS</h1>
        <p className="muted">Carregando painel comercial...</p>
      </div>
    );
  }

  return (
    <div className="container dashboard-container">
      <div className="page-header">
        <div>
          <p className="eyebrow">Produto SaaS</p>
          <h1>{overview.workspace.brand_name}</h1>
          <p className="muted">
            Configure assinatura, limites, canais de entrega, relatórios e segmentos sem transformar o produto em fintech.
          </p>
        </div>
        <strong className="status-pill good">{planLabels[overview.workspace.plan]}</strong>
      </div>

      <section className="metric-grid">
        {Object.entries(overview.limits).map(([key, limit]) => {
          const used = overview.usage[key] ?? 0;
          return (
            <div className="metric-card" key={key}>
              <span className="metric-label">{usageLabels[key] ?? key}</span>
              <strong>{used}/{limit}</strong>
              <meter min={0} max={100} value={pct(used, limit)} />
            </div>
          );
        })}
      </section>

      <section className="dashboard-grid">
        <div className="panel">
          <h2>Planos</h2>
          <div className="plan-grid">
            {(['FREE', 'PRO', 'ADVISOR'] as SubscriptionPlan[]).map((plan) => (
              <button
                type="button"
                className={`plan-card ${overview.workspace.plan === plan ? 'active' : ''}`}
                key={plan}
                onClick={() => changePlan(plan)}
              >
                <strong>{planLabels[plan]}</strong>
                <span>
                  {plan === 'FREE' && 'Para validação e uso individual.'}
                  {plan === 'PRO' && 'Para investidores ativos e traders.'}
                  {plan === 'ADVISOR' && 'Para assessores, criadores e grupos.'}
                </span>
              </button>
            ))}
          </div>
        </div>

        <div className="panel">
          <h2>Marca</h2>
          <form className="stack-form" onSubmit={saveWorkspace}>
            <input name="name" defaultValue={overview.workspace.name} placeholder="Workspace" />
            <input name="brand_name" defaultValue={overview.workspace.brand_name} placeholder="Marca exibida" />
            <button type="submit">Salvar</button>
          </form>
        </div>
      </section>

      <section className="dashboard-grid">
        <div className="panel">
          <h2>Canais de alerta</h2>
          <form onSubmit={addChannel}>
            <select name="channel_type" defaultValue="TELEGRAM">
              <option value="TELEGRAM">Telegram</option>
              <option value="EMAIL">Email</option>
              <option value="WEBHOOK">Webhook</option>
            </select>
            <input name="destination" placeholder="@usuario, email ou URL" required />
            <button type="submit">Adicionar</button>
          </form>
          <ul className="source-list">
            {overview.channels.length === 0 ? (
              <li className="muted">Nenhum canal configurado.</li>
            ) : (
              overview.channels.map((channel) => (
                <li key={channel.id}>
                  <strong>{channel.channel_type}</strong>
                  <span>{channel.destination}</span>
                </li>
              ))
            )}
          </ul>
        </div>

        <div className="panel">
          <h2>Templates de relatório</h2>
          <form className="stack-form" onSubmit={addTemplate}>
            <input name="title" placeholder="Resumo semanal Nasdaq" required />
            <input name="audience" placeholder="Investidores iniciantes" />
            <label className="checkbox-row">
              <input type="checkbox" name="include_ai_summary" defaultChecked />
              Resumo IA
            </label>
            <label className="checkbox-row">
              <input type="checkbox" name="include_backtest" />
              Backtest
            </label>
            <button type="submit">Criar</button>
          </form>
          <ul className="source-list">
            {overview.report_templates.map((template) => (
              <li key={template.id}>
                <strong>{template.title}</strong>
                <span>{template.audience}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="panel">
        <h2>Segmentos</h2>
        <form onSubmit={addSegment}>
          <input name="name" placeholder="Swing trade" required />
          <input name="description" placeholder="Perfil, objetivo ou lista modelo" />
          <button type="submit">Adicionar</button>
        </form>
        <div className="table-scroll compact-scroll">
          <table className="table dense-table">
            <thead>
              <tr><th>Nome</th><th>Descrição</th></tr>
            </thead>
            <tbody>
              {overview.segments.length === 0 ? (
                <tr><td colSpan={2} className="muted">Disponível no plano Advisor.</td></tr>
              ) : (
                overview.segments.map((segment) => (
                  <tr key={segment.id}><td>{segment.name}</td><td className="muted">{segment.description}</td></tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
