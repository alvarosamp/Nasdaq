"""Session-based login (replaces the old HTTP Basic Auth in app/security.py).

Auth model: the first account ever created (via /cadastro, only while the
users table is empty) becomes admin. After that, /cadastro closes itself and
only an already-logged-in admin can create further accounts (via /usuarios) —
so the public internet-facing app never has an open signup form.
"""
from __future__ import annotations

import secrets
import time
from collections import defaultdict

import bcrypt
from fastapi import Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User

# bcrypt truncates/rejects input over 72 bytes; long passwords are hashed first
# so length never causes a hard failure at hash/verify time.
_MAX_PASSWORD_BYTES = 72


def _prepare(password: str) -> bytes:
    encoded = password.encode("utf-8")
    if len(encoded) > _MAX_PASSWORD_BYTES:
        import hashlib

        encoded = hashlib.sha256(encoded).digest()
    return encoded


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_prepare(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(_prepare(password), password_hash.encode("utf-8"))
    except ValueError:
        return False


class RedirectToLogin(Exception):
    """Raised by require_login/require_admin when there's no valid session.

    Caught by an exception handler (registered in app/main.py) that turns it
    into a redirect to /login — these routes serve HTML, so a raw 401 would
    just show an ugly error page instead of sending the user to log in.
    """

    def __init__(self, next_path: str = "/"):
        self.next_path = next_path


def get_csrf_token(request: Request) -> str:
    token = request.session.get("csrf_token")
    if not token:
        token = secrets.token_hex(16)
        request.session["csrf_token"] = token
    return token


def verify_csrf(request: Request, submitted_token: str) -> bool:
    expected = request.session.get("csrf_token")
    return bool(expected) and secrets.compare_digest(expected, submitted_token)


def require_login(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = request.session.get("user_id")
    user = db.get(User, user_id) if user_id else None
    if user is None:
        raise RedirectToLogin(next_path=str(request.url.path))
    return user


def require_admin(request: Request, db: Session = Depends(get_db)) -> User:
    user = require_login(request, db)
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Requer permissão de administrador")
    return user


def require_login_api(request: Request, db: Session = Depends(get_db)) -> User:
    """Same check as require_login, but for JSON endpoints called via fetch().

    A redirect response would be silently followed by fetch() and mistaken
    for a successful JSON reply, so these routes need a real 401 instead.
    """
    user_id = request.session.get("user_id")
    user = db.get(User, user_id) if user_id else None
    if user is None:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return user


# --- Rate limiting simples de tentativas de login (em memória, por processo) ---
_MAX_ATTEMPTS = 5
_LOCKOUT_SECONDS = 300
_failed_attempts: dict[str, list[float]] = defaultdict(list)


def is_locked_out(username: str) -> bool:
    now = time.time()
    attempts = [t for t in _failed_attempts[username] if now - t < _LOCKOUT_SECONDS]
    _failed_attempts[username] = attempts
    return len(attempts) >= _MAX_ATTEMPTS


def register_failed_attempt(username: str) -> None:
    _failed_attempts[username].append(time.time())


def clear_failed_attempts(username: str) -> None:
    _failed_attempts.pop(username, None)
