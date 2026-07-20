import type { RuleType } from '../types';
import { RULE_META, type RuleConditionsBuilder } from '../hooks/useRuleConditions';

export function RuleConditionBuilder({ builder }: { builder: RuleConditionsBuilder }) {
  return (
    <div>
      <label className="field-label">
        Se... (lógica entre as condições abaixo)
        <select value={builder.logic} onChange={(e) => builder.setLogic(e.target.value as 'ALL' | 'ANY')}>
          <option value="ALL">TODAS as condições (E)</option>
          <option value="ANY">QUALQUER condição (OU)</option>
        </select>
      </label>

      <div>
        {builder.rows.map((row) => {
          const meta = RULE_META[row.rule_type];
          return (
            <div className="condition-row" key={row.key}>
              <select
                value={row.rule_type}
                onChange={(e) => builder.updateCondition(row.key, { rule_type: e.target.value as RuleType })}
              >
                {Object.entries(RULE_META).map(([value, m]) => (
                  <option key={value} value={value}>
                    {m.name}
                  </option>
                ))}
              </select>
              {meta.threshold && (
                <label className="field-label">
                  {meta.threshold}
                  <input
                    type="number"
                    step="0.01"
                    value={row.threshold}
                    onChange={(e) => builder.updateCondition(row.key, { threshold: parseFloat(e.target.value) || 0 })}
                  />
                </label>
              )}
              {meta.a && (
                <label className="field-label">
                  {meta.a}
                  <input
                    type="number"
                    value={row.param_a}
                    onChange={(e) => builder.updateCondition(row.key, { param_a: parseInt(e.target.value, 10) || 0 })}
                  />
                </label>
              )}
              {meta.b && (
                <label className="field-label">
                  {meta.b}
                  <input
                    type="number"
                    value={row.param_b}
                    onChange={(e) => builder.updateCondition(row.key, { param_b: parseInt(e.target.value, 10) || 0 })}
                  />
                </label>
              )}
              <button
                type="button"
                className="link-btn danger"
                onClick={() => builder.removeCondition(row.key)}
                disabled={builder.rows.length <= 1}
              >
                remover condição
              </button>
            </div>
          );
        })}
      </div>

      <button type="button" className="btn-secondary" onClick={builder.addCondition}>
        + condição
      </button>

      <label className="field-label" style={{ marginTop: '0.75rem' }}>
        Cooldown entre alertas (minutos)
        <input
          type="number"
          value={builder.cooldownMinutes}
          onChange={(e) => builder.setCooldownMinutes(parseInt(e.target.value, 10) || 60)}
        />
      </label>
    </div>
  );
}
