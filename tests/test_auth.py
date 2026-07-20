import re

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


def _extract_csrf(html: str) -> str:
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    assert match, "csrf_token não encontrado na página"
    return match.group(1)


def test_cadastro_open_when_no_users(client):
    test_client, _ = client
    res = test_client.get("/cadastro")
    assert res.status_code == 200
    assert "Criar a primeira conta" in res.text


def test_cadastro_creates_first_user_as_admin(client):
    test_client, Session = client
    csrf = _extract_csrf(test_client.get("/cadastro").text)

    res = test_client.post(
        "/cadastro",
        data={"username": "admin", "password": "senha12345", "password_confirm": "senha12345", "csrf_token": csrf},
        follow_redirects=False,
    )
    assert res.status_code == 302
    assert res.headers["location"] == "/"

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

    res = test_client.get("/cadastro")
    assert res.status_code == 200
    assert "Cadastro fechado" in res.text

    csrf = _extract_csrf(test_client.get("/login").text)
    res = test_client.post(
        "/cadastro",
        data={"username": "outro", "password": "senha12345", "password_confirm": "senha12345", "csrf_token": csrf},
        follow_redirects=False,
    )
    assert res.status_code == 403


def test_login_success_allows_protected_route(client):
    test_client, Session = client
    db = Session()
    db.add(User(username="pai", password_hash=auth_module.hash_password("senha12345"), is_admin=True))
    db.commit()
    db.close()

    csrf = _extract_csrf(test_client.get("/login").text)
    res = test_client.post(
        "/login",
        data={"username": "pai", "password": "senha12345", "csrf_token": csrf},
        follow_redirects=False,
    )
    assert res.status_code == 302
    assert res.headers["location"] == "/"

    home = test_client.get("/")
    assert home.status_code == 200
    assert "Watchlist" in home.text


def test_login_wrong_password_rejected(client):
    test_client, Session = client
    db = Session()
    db.add(User(username="pai", password_hash=auth_module.hash_password("senha12345"), is_admin=True))
    db.commit()
    db.close()

    csrf = _extract_csrf(test_client.get("/login").text)
    res = test_client.post(
        "/login",
        data={"username": "pai", "password": "errada", "csrf_token": csrf},
        follow_redirects=False,
    )
    assert res.status_code == 401
    assert "inválidos" in res.text


def test_protected_page_redirects_when_not_logged_in(client):
    test_client, _ = client
    res = test_client.get("/", follow_redirects=False)
    assert res.status_code == 302
    assert res.headers["location"].startswith("/login")


def test_api_route_returns_401_json_when_not_logged_in(client):
    test_client, _ = client
    res = test_client.get("/api/dashboard-summary")
    assert res.status_code == 401


def test_usuarios_requires_admin(client):
    test_client, Session = client
    db = Session()
    db.add(User(username="comum", password_hash=auth_module.hash_password("senha12345"), is_admin=False))
    db.commit()
    db.close()

    csrf = _extract_csrf(test_client.get("/login").text)
    test_client.post("/login", data={"username": "comum", "password": "senha12345", "csrf_token": csrf})

    res = test_client.get("/usuarios")
    assert res.status_code == 403


def test_admin_can_create_new_user_via_usuarios_page(client):
    test_client, Session = client
    db = Session()
    db.add(User(username="admin", password_hash=auth_module.hash_password("senha12345"), is_admin=True))
    db.commit()
    db.close()

    csrf = _extract_csrf(test_client.get("/login").text)
    test_client.post("/login", data={"username": "admin", "password": "senha12345", "csrf_token": csrf})

    page = test_client.get("/usuarios")
    csrf2 = _extract_csrf(page.text)
    res = test_client.post(
        "/usuarios",
        data={"username": "novo", "password": "outrasenha1", "csrf_token": csrf2},
        follow_redirects=False,
    )
    assert res.status_code == 302

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
        csrf = _extract_csrf(test_client.get("/login").text)
        test_client.post("/login", data={"username": "pai", "password": "errada", "csrf_token": csrf})

    csrf = _extract_csrf(test_client.get("/login").text)
    res = test_client.post(
        "/login",
        data={"username": "pai", "password": "senha12345", "csrf_token": csrf},
    )
    assert res.status_code == 429
    assert "Muitas tentativas" in res.text
