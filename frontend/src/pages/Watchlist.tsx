import { useEffect, useState, type FormEvent } from 'react';
import { api, ApiError } from '../api/client';
import { useToast } from '../context/ToastContext';
import { useConfirm } from '../components/ConfirmModal';
import { RuleConditionBuilder } from '../components/RuleConditionBuilder';
import { useRuleConditions } from '../hooks/useRuleConditions';
import type { BacktestResult, WatchlistItem } from '../types';

export function Watchlist() {
  const toast = useToast();
  const confirm = useConfirm();
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [symbol, setSymbol] = useState('');
  const [label, setLabel] = useState('');
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [backtestResult, setBacktestResult] = useState<BacktestResult | null>(null);
  const [backtesting, setBacktesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const builder = useRuleConditions();

  async function loadItems() {
    try {
      setItems(await api.get<WatchlistItem[]>('/api/watchlist'));
    } catch {
      toast('Erro ao carregar watchlist', 'error');
    }
  }

  useEffect(() => {
    loadItems();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleAdd(e: FormEvent) {
    e.preventDefault();
    try {
      await api.post('/api/watchlist', { symbol, label });
      toast(`${symbol.toUpperCase()} adicionado à watchlist`, 'success');
      setSymbol('');
      setLabel('');
      loadItems();
    } catch {
      toast('Erro ao adicionar ativo', 'error');
    }
  }

  async function handleRemove(item: WatchlistItem) {
    const ok = await confirm(`Remover ${item.symbol} da watchlist? Isso também remove as regras associadas.`);
    if (!ok) return;
    try {
      await api.delete(`/api/watchlist/${item.id}`);
      toast(`${item.symbol} removido`, 'success');
      loadItems();
    } catch {
      toast('Erro ao remover ativo', 'error');
    }
  }

  function openRuleForm(item: WatchlistItem) {
    setExpandedId(item.id);
    setBacktestResult(null);
    builder.reset();
  }

  async function handleTestRule(item: WatchlistItem) {
    setBacktesting(true);
    setBacktestResult(null);
    try {
      const result = await api.post<BacktestResult>('/api/watchlist/rules/backtest', {
        symbol: item.symbol,
        logic: builder.logic,
        conditions: builder.conditions,
        period: '3mo',
        interval: '1d',
        forward_bars: 5,
      });
      setBacktestResult(result);
    } catch {
      toast('Erro ao testar regra', 'error');
    } finally {
      setBacktesting(false);
    }
  }

  async function handleSaveRule(item: WatchlistItem) {
    if (builder.conditions.length === 0) {
      toast('Adicione ao menos uma condição', 'error');
      return;
    }
    setSaving(true);
    try {
      await api.post(`/api/watchlist/${item.id}/rules`, {
        watchlist_item_id: item.id,
        logic: builder.logic,
        cooldown_minutes: builder.cooldownMinutes,
        conditions: builder.conditions,
      });
      toast(`Regra criada para ${item.symbol}`, 'success');
    } catch (err) {
      toast(err instanceof ApiError ? err.message : 'Erro ao criar regra', 'error');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="container">
      <h1>Watchlist &amp; Regras de Alerta</h1>

      <section>
        <h2>Adicionar ativo</h2>
        <form onSubmit={handleAdd}>
          <input
            type="text"
            placeholder="Símbolo (ex: AAPL)"
            required
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
          />
          <input type="text" placeholder="Rótulo (opcional)" value={label} onChange={(e) => setLabel(e.target.value)} />
          <button type="submit">Adicionar</button>
        </form>
      </section>

      <section>
        <h2>Ativos monitorados</h2>
        <ul className="items-list">
          {items.length === 0 && <li className="muted">Nenhum ativo cadastrado ainda.</li>}
          {items.map((item) => (
            <li key={item.id}>
              <strong>{item.symbol}</strong> {item.label}
              <button type="button" className="link-btn" onClick={() => openRuleForm(item)}>
                + regra
              </button>
              <button type="button" className="link-btn danger" onClick={() => handleRemove(item)}>
                remover
              </button>

              {expandedId === item.id && (
                <div className="rule-form">
                  <RuleConditionBuilder builder={builder} />
                  <div className="chart-controls">
                    <button
                      type="button"
                      className="btn-secondary"
                      disabled={backtesting}
                      onClick={() => handleTestRule(item)}
                    >
                      {backtesting ? 'Testando...' : 'Testar regra'}
                    </button>
                    <button type="button" disabled={saving} onClick={() => handleSaveRule(item)}>
                      {saving ? 'Salvando...' : 'Salvar regra'}
                    </button>
                  </div>
                  {backtestResult && (
                    <p className="muted">
                      Essa regra teria disparado <strong>{backtestResult.trigger_count}</strong> vez(es) nos últimos
                      3 meses. Retorno:{' '}
                      {backtestResult.avg_forward_return_pct === null
                        ? 'sem dados suficientes'
                        : `${backtestResult.avg_forward_return_pct >= 0 ? '+' : ''}${backtestResult.avg_forward_return_pct.toFixed(2)}% em média, 5 pregões depois`}
                      . (Não é garantia de resultado futuro.)
                    </p>
                  )}
                </div>
              )}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
