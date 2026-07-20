"""JWT-based auth for the API-only backend (frontend is a separate SPA).

Auth model: the first account ever created (via POST /api/auth/cadastro,
only while the users table is empty) becomes admin. After that, cadastro
closes itself and only an already-logged-in admin can create further
accounts (via /api/auth/usuarios) — so the public internet-facing API never
has an open signup endpoint.
"""
from __future__ import annotations

import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import User

# bcrypt truncates/rejects input over 72 bytes; long passwords are hashed first
# so length never causes a hard failure at hash/verify time.
_MAX_PASSWORD_BYTES = 72
_JWT_ALGORITHM = "HS256"


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


def create_access_token(user_id: int) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expire_hours)
    payload = {"sub": str(user_id), "exp": expires_at}
    return jwt.encode(payload, settings.secret_key, algorithm=_JWT_ALGORITHM)


def _decode_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[_JWT_ALGORITHM])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None


def get_current_user(
    authorization: str | None = Header(default=None), db: Session = Depends(get_db)
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Não autenticado")

    token = authorization.removeprefix("Bearer ").strip()
    user_id = _decode_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    return user


def require_admin_user(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Requer permissão de administrador")
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
