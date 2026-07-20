import { act, renderHook } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { useRuleConditions } from './useRuleConditions';

describe('useRuleConditions', () => {
  it('starts with one default PRICE_ABOVE condition and ALL logic', () => {
    const { result } = renderHook(() => useRuleConditions());

    expect(result.current.logic).toBe('ALL');
    expect(result.current.conditions).toHaveLength(1);
    expect(result.current.conditions[0]).toEqual({
      rule_type: 'PRICE_ABOVE',
      threshold: 0,
      param_a: 0,
      param_b: 0,
    });
  });

  it('addCondition() appends a new row without touching existing ones', () => {
    const { result } = renderHook(() => useRuleConditions());

    act(() => {
      result.current.updateCondition(result.current.rows[0].key, { rule_type: 'RSI_OVERBOUGHT', threshold: 70 });
    });
    act(() => {
      result.current.addCondition();
    });

    expect(result.current.conditions).toHaveLength(2);
    expect(result.current.conditions[0]).toMatchObject({ rule_type: 'RSI_OVERBOUGHT', threshold: 70 });
    expect(result.current.conditions[1]).toMatchObject({ rule_type: 'PRICE_ABOVE' });
  });

  it('removeCondition() removes only the targeted row', () => {
    const { result } = renderHook(() => useRuleConditions());
    act(() => result.current.addCondition());
    const [first, second] = result.current.rows;

    act(() => result.current.removeCondition(first.key));

    expect(result.current.rows).toHaveLength(1);
    expect(result.current.rows[0].key).toBe(second.key);
  });

  it('removeCondition() refuses to remove the last remaining row', () => {
    const { result } = renderHook(() => useRuleConditions());
    const onlyRow = result.current.rows[0];

    act(() => result.current.removeCondition(onlyRow.key));

    expect(result.current.rows).toHaveLength(1);
  });

  it('updateCondition() patches a single field on the targeted row', () => {
    const { result } = renderHook(() => useRuleConditions());
    const key = result.current.rows[0].key;

    act(() => result.current.updateCondition(key, { param_a: 14 }));

    expect(result.current.conditions[0].param_a).toBe(14);
    expect(result.current.conditions[0].rule_type).toBe('PRICE_ABOVE'); // unrelated field untouched
  });

  it('setLogic() and setCooldownMinutes() update independently of the conditions payload', () => {
    const { result } = renderHook(() => useRuleConditions());

    act(() => result.current.setLogic('ANY'));
    act(() => result.current.setCooldownMinutes(120));

    expect(result.current.logic).toBe('ANY');
    expect(result.current.cooldownMinutes).toBe(120);
    expect(result.current.conditions).toHaveLength(1);
  });

  it('reset() clears back to the initial single-condition ALL state', () => {
    const { result } = renderHook(() => useRuleConditions());
    act(() => result.current.addCondition());
    act(() => result.current.setLogic('ANY'));
    act(() => result.current.setCooldownMinutes(999));

    act(() => result.current.reset());

    expect(result.current.logic).toBe('ALL');
    expect(result.current.cooldownMinutes).toBe(60);
    expect(result.current.conditions).toHaveLength(1);
  });

  it('conditions payload never leaks the internal row key', () => {
    const { result } = renderHook(() => useRuleConditions());
    act(() => result.current.addCondition());

    for (const condition of result.current.conditions) {
      expect(condition).not.toHaveProperty('key');
    }
  });
});
