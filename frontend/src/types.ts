// Mirrors app/schemas.py and app/models.py on the backend — keep in sync manually.

export type RuleType =
  | 'PRICE_ABOVE'
  | 'PRICE_BELOW'
  | 'PCT_CHANGE'
  | 'RSI_OVERBOUGHT'
  | 'RSI_OVERSOLD'
  | 'MA_CROSS_UP'
  | 'MA_CROSS_DOWN'
  | 'MACD_CROSS_UP'
  | 'MACD_CROSS_DOWN'
  | 'VOLUME_SPIKE';

export type RuleLogic = 'ALL' | 'ANY';

export type TransactionSide = 'BUY' | 'SELL';

export interface User {
  id: number;
  username: string;
  is_admin: boolean;
  created_at: string;
}

export interface WatchlistItem {
  id: number;
  symbol: string;
  label: string;
  active: boolean;
}

export interface Condition {
  rule_type: RuleType;
  threshold: number;
  param_a: number;
  param_b: number;
}

export interface ConditionOut extends Condition {
  id: number;
}

export interface AlertRule {
  id: number;
  watchlist_item_id: number;
  logic: RuleLogic;
  active: boolean;
  cooldown_minutes: number;
  last_triggered_at: string | null;
  conditions: ConditionOut[];
}

export interface BacktestOccurrence {
  date: string;
  price: number;
  forward_return_pct: number | null;
}

export interface BacktestResult {
  trigger_count: number;
  avg_forward_return_pct: number | null;
  occurrences: BacktestOccurrence[];
}

export interface AlertLog {
  id: number;
  symbol: string;
  rule_type: string;
  message: string;
  triggered_at: string;
  delivered_telegram: boolean;
}

export interface NewsItem {
  symbol: string;
  headline: string;
  url: string;
  source: string;
  published_at: string;
}

export interface GlobalNewsItem {
  category: string;
  headline: string;
  summary: string;
  url: string;
  source: string;
  impact_score: number;
  published_at: string;
}

export interface EconomicEvent {
  event_name: string;
  country: string;
  event_date: string;
  impact: string;
  forecast: string;
  previous: string;
}

export interface EarningsEvent {
  symbol: string;
  event_date: string;
  eps_estimate: number | null;
  revenue_estimate: number | null;
}

export interface Transaction {
  id: number;
  symbol: string;
  side: TransactionSide;
  quantity: number;
  price: number;
  executed_at: string;
  notes: string;
}

export interface PositionSummary {
  symbol: string;
  quantity: number;
  avg_cost: number;
  current_price: number | null;
  market_value: number | null;
  unrealized_pnl: number | null;
  realized_pnl: number;
}

export interface DashboardRow {
  id: number;
  symbol: string;
  label: string;
  price: number | null;
  change_pct: number | null;
  taken_at: string | null;
}

export interface DashboardSummary {
  rows: DashboardRow[];
  alerts: {
    symbol: string;
    message: string;
    triggered_at: string;
    delivered_telegram: boolean;
  }[];
}

export interface ChartData {
  symbol: string;
  timestamps: string[];
  open: (number | null)[];
  high: (number | null)[];
  low: (number | null)[];
  close: (number | null)[];
  volume: (number | null)[];
  rsi: (number | null)[];
  macd: (number | null)[];
  macd_signal: (number | null)[];
  ema_fast: (number | null)[];
  ema_slow: (number | null)[];
}
