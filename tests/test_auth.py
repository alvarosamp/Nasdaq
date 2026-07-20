import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import auth as auth_module
from app.db import Base, get_db
from app.main import app
from app.models import User


@pytest.fixture()
def client():
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
    # Clear any brute-force lockout state left over from other tests (module-level dict).
    auth_module._failed_attempts.clear()

    test_client = TestClient(app)
    yield test_client, TestingSession

    app.dependency_overrides.clear()


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_cadastro_creates_first_user_as_admin(client):
    test_client, Session = client
    res = test_client.post("/api/auth/cadastro", json={"username": "admin", "password": "senha12345"})
    assert res.status_code == 201
    data = res.json()
    assert data["user"]["username"] == "admin"
    assert data["user"]["is_admin"] is True
    assert data["access_token"]

    db = Session()
    user = db.query(User).filter(User.username == "admin").first()
    assert user is not None
    assert user.is_admin is True
    db.close()


def test_cadastro_closes_after_first_user(client):
    test_client, Session = client
    db = Session()
    db.add(User(username="admin", password_hash=auth_module.hash_password("senha12345"), is_admin=True))
    db.commit()
    db.close()

    res = test_client.post("/api/auth/cadastro", json={"username": "outro", "password": "senha12345"})
    assert res.status_code == 403


def test_login_success_returns_token_that_works_on_protected_route(client):
    test_client, Session = client
    db = Session()
    db.add(User(username="pai", password_hash=auth_module.hash_password("senha12345"), is_admin=True))
    db.commit()
    db.close()

    res = test_client.post("/api/auth/login", json={"username": "pai", "password": "senha12345"})
    assert res.status_code == 200
    token = res.json()["access_token"]

    me = test_client.get("/api/auth/me", headers=_auth_headers(token))
    assert me.status_code == 200
    assert me.json()["username"] == "pai"

    watchlist = test_client.get("/api/watchlist", headers=_auth_headers(token))
    assert watchlist.status_code == 200


def test_login_wrong_password_rejected(client):
    test_client, Session = client
    db = Session()
    db.add(User(username="pai", password_hash=auth_module.hash_password("senha12345"), is_admin=True))
    db.commit()
    db.close()

    res = test_client.post("/api/auth/login", json={"username": "pai", "password": "errada"})
    assert res.status_code == 401


def test_protected_route_rejects_missing_token(client):
    test_client, _ = client
    res = test_client.get("/api/dashboard-summary")
    assert res.status_code == 401


def test_protected_route_rejects_garbage_token(client):
    test_client, _ = client
    res = test_client.get("/api/dashboard-summary", headers=_auth_headers("not-a-real-token"))
    assert res.status_code == 401


def test_usuarios_requires_admin(client):
    test_client, Session = client
    db = Session()
    db.add(User(username="comum", password_hash=auth_module.hash_password("senha12345"), is_admin=False))
    db.commit()
    db.close()

    login = test_client.post("/api/auth/login", json={"username": "comum", "password": "senha12345"})
    token = login.json()["access_token"]

    res = test_client.get("/api/auth/usuarios", headers=_auth_headers(token))
    assert res.status_code == 403


def test_admin_can_create_new_user_via_usuarios_endpoint(client):
    test_client, Session = client
    db = Session()
    db.add(User(username="admin", password_hash=auth_module.hash_password("senha12345"), is_admin=True))
    db.commit()
    db.close()

    login = test_client.post("/api/auth/login", json={"username": "admin", "password": "senha12345"})
    token = login.json()["access_token"]

    res = test_client.post(
        "/api/auth/usuarios",
        json={"username": "novo", "password": "outrasenha1", "is_admin": False},
        headers=_auth_headers(token),
    )
    assert res.status_code == 201

    db = Session()
    assert db.query(User).filter(User.username == "novo").first() is not None
    db.close()


def test_login_rate_limit_locks_out_after_repeated_failures(client):
    test_client, Session = client
    db = Session()
    db.add(User(username="pai", password_hash=auth_module.hash_password("senha12345"), is_admin=True))
    db.commit()
    db.close()

    for _ in range(5):
        test_client.post("/api/auth/login", json={"username": "pai", "password": "errada"})

    res = test_client.post("/api/auth/login", json={"username": "pai", "password": "senha12345"})
    assert res.status_code == 429
