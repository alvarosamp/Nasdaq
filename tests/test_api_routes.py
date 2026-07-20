import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models import AlertLog, PriceSnapshot, WatchlistItem
from app.security import require_dashboard_auth


@pytest.fixture()
def client():
    # StaticPool keeps a single shared connection alive so every session sees
    # the same in-memory sqlite database (plain :memory: gives each new
    # connection its own empty database).
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[require_dashboard_auth] = lambda: "test-user"

    # Deliberately NOT using TestClient as a context manager: that would trigger
    # app.main's lifespan (real DB init, real scheduler, real Telegram polling
    # using whatever is in .env) which we don't want running during unit tests.
    test_client = TestClient(app)
    yield test_client, TestingSession

    app.dependency_overrides.clear()


def test_dashboard_summary_empty(client):
    test_client, _ = client
    res = test_client.get("/api/dashboard-summary")
    assert res.status_code == 200
    assert res.json() == {"rows": [], "alerts": []}


def test_dashboard_summary_with_data(client):
    test_client, Session = client
    db = Session()
    item = WatchlistItem(symbol="AAPL", label="Apple")
    db.add(item)
    db.commit()
    db.add(PriceSnapshot(watchlist_item_id=item.id, price=150.5, change_pct=1.2, volume=1000))
    db.commit()
    db.close()

    res = test_client.get("/api/dashboard-summary")
    assert res.status_code == 200
    data = res.json()
    assert len(data["rows"]) == 1
    assert data["rows"][0]["symbol"] == "AAPL"
    assert data["rows"][0]["price"] == 150.5


def test_alerts_filter_by_symbol(client):
    test_client, Session = client
    db = Session()
    db.add(AlertLog(symbol="AAPL", rule_type="PRICE_ABOVE", message="AAPL subiu"))
    db.add(AlertLog(symbol="MSFT", rule_type="PRICE_ABOVE", message="MSFT subiu"))
    db.commit()
    db.close()

    res = test_client.get("/api/alerts", params={"symbol": "aapl"})
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["symbol"] == "AAPL"


def test_alerts_filter_by_rule_type(client):
    test_client, Session = client
    db = Session()
    db.add(AlertLog(symbol="AAPL", rule_type="PRICE_ABOVE", message="a"))
    db.add(AlertLog(symbol="AAPL", rule_type="RSI_OVERBOUGHT", message="b"))
    db.commit()
    db.close()

    res = test_client.get("/api/alerts", params={"rule_type": "RSI_OVERBOUGHT"})
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["rule_type"] == "RSI_OVERBOUGHT"


def test_alerts_no_filter_returns_all(client):
    test_client, Session = client
    db = Session()
    db.add(AlertLog(symbol="AAPL", rule_type="PRICE_ABOVE", message="a"))
    db.add(AlertLog(symbol="MSFT", rule_type="PRICE_ABOVE", message="b"))
    db.commit()
    db.close()

    res = test_client.get("/api/alerts")
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_news_endpoint_empty(client):
    test_client, _ = client
    res = test_client.get("/api/news")
    assert res.status_code == 200
    assert res.json() == []
