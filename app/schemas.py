from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models import RuleType


class WatchlistItemCreate(BaseModel):
    symbol: str
    label: str = ""


class WatchlistItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    label: str
    active: bool


class AlertRuleCreate(BaseModel):
    watchlist_item_id: int
    rule_type: RuleType
    threshold: float = 0.0
    param_a: int = 0
    param_b: int = 0
    cooldown_minutes: int = 60


class AlertRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    watchlist_item_id: int
    rule_type: RuleType
    threshold: float
    param_a: int
    param_b: int
    active: bool
    cooldown_minutes: int
    last_triggered_at: datetime | None


class AlertLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    rule_type: str
    message: str
    triggered_at: datetime
    delivered_telegram: bool


class PriceSnapshotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    price: float
    change_pct: float
    volume: float
    taken_at: datetime
