import { useCallback, useState } from 'react';
import type { Condition, RuleLogic, RuleType } from '../types';

export interface RuleMeta {
  name: string;
  threshold?: string;
  a?: string;
  b?: string;
}

export const RULE_META: Record<RuleType, RuleMeta> = {
  PRICE_ABOVE: { name: 'Preço acima de', threshold: 'Preço (US$)' },
  PRICE_BELOW: { name: 'Preço abaixo de', threshold: 'Preço (US$)' },
  PCT_CHANGE: { name: 'Variação percentual (qualquer direção)', threshold: 'Variação mínima (%)' },
  RSI_OVERBOUGHT: {
    name: 'RSI sobrecomprado',
    threshold: 'Limite do RSI (padrão 70)',
    a: 'Período do RSI (padrão 14)',
  },
  RSI_OVERSOLD: {
    name: 'RSI sobrevendido',
    threshold: 'Limite do RSI (padrão 30)',
    a: 'Período do RSI (padrão 14)',
  },
  MA_CROSS_UP: {
    name: 'Golden cross (média rápida cruza acima da lenta)',
    a: 'EMA rápida (padrão 9)',
    b: 'EMA lenta (padrão 21)',
  },
  MA_CROSS_DOWN: {
    name: 'Death cross (média rápida cruza abaixo da lenta)',
    a: 'EMA rápida (padrão 9)',
    b: 'EMA lenta (padrão 21)',
  },
  MACD_CROSS_UP: { name: 'MACD cruza acima da linha de sinal' },
  MACD_CROSS_DOWN: { name: 'MACD cruza abaixo da linha de sinal' },
  VOLUME_SPIKE: { name: 'Spike de volume', threshold: 'Múltiplo da média (padrão 3x)', a: 'Período (padrão 20)' },
};

const EMPTY_CONDITION: Condition = { rule_type: 'PRICE_ABOVE', threshold: 0, param_a: 0, param_b: 0 };

let nextId = 0;

interface ConditionRow extends Condition {
  key: number;
}

export function useRuleConditions() {
  const [logic, setLogic] = useState<RuleLogic>('ALL');
  const [cooldownMinutes, setCooldownMinutes] = useState(60);
  const [rows, setRows] = useState<ConditionRow[]>([{ ...EMPTY_CONDITION, key: nextId++ }]);

  const addCondition = useCallback(() => {
    setRows((prev) => [...prev, { ...EMPTY_CONDITION, key: nextId++ }]);
  }, []);

  const removeCondition = useCallback((key: number) => {
    setRows((prev) => (prev.length > 1 ? prev.filter((r) => r.key !== key) : prev));
  }, []);

  const updateCondition = useCallback((key: number, patch: Partial<Condition>) => {
    setRows((prev) => prev.map((r) => (r.key === key ? { ...r, ...patch } : r)));
  }, []);

  const reset = useCallback(() => {
    setLogic('ALL');
    setCooldownMinutes(60);
    setRows([{ ...EMPTY_CONDITION, key: nextId++ }]);
  }, []);

  const conditions: Condition[] = rows.map(({ key, ...c }) => {
    void key;
    return c;
  });

  return {
    logic,
    setLogic,
    cooldownMinutes,
    setCooldownMinutes,
    rows,
    addCondition,
    removeCondition,
    updateCondition,
    reset,
    conditions,
  };
}

export type RuleConditionsBuilder = ReturnType<typeof useRuleConditions>;
