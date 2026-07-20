from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import (
    clear_failed_attempts,
    create_access_token,
    get_current_user,
    hash_password,
    is_locked_out,
    register_failed_attempt,
    require_admin_user,
    verify_password,
)
from app.db import get_db
from app.models import User
from app.schemas import CadastroRequest, LoginRequest, TokenResponse, UserOut, UsuarioCreateRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    username_norm = payload.username.strip().lower()

    if is_locked_out(username_norm):
        raise HTTPException(
            status_code=429, detail="Muitas tentativas incorretas. Aguarde alguns minutos e tente de novo."
        )

    user = db.query(User).filter(User.username == username_norm).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        register_failed_attempt(username_norm)
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos.")

    clear_failed_attempts(username_norm)
    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/cadastro", response_model=TokenResponse, status_code=201)
def cadastro(payload: CadastroRequest, db: Session = Depends(get_db)):
    if db.query(User).count() > 0:
        raise HTTPException(
            status_code=403,
            detail="Cadastro fechado — já existe uma conta configurada. Peça a um administrador.",
        )

    username_norm = payload.username.strip().lower()
    if db.query(User).filter(User.username == username_norm).first():
        raise HTTPException(status_code=400, detail="Já existe um usuário com esse nome.")

    # Re-checa antes de inserir pra reduzir (não eliminar totalmente) a corrida entre dois
    # cadastros simultâneos criando dois "primeiros" admins ao mesmo tempo.
    if db.query(User).count() > 0:
        raise HTTPException(status_code=403, detail="Cadastro fechado — já existe uma conta configurada.")

    user = User(username=username_norm, password_hash=hash_password(payload.password), is_admin=True)
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.get("/usuarios", response_model=list[UserOut])
def list_usuarios(admin: User = Depends(require_admin_user), db: Session = Depends(get_db)):
    return db.query(User).order_by(User.created_at).all()


@router.post("/usuarios", response_model=UserOut, status_code=201)
def create_usuario(
    payload: UsuarioCreateRequest, admin: User = Depends(require_admin_user), db: Session = Depends(get_db)
):
    username_norm = payload.username.strip().lower()
    if db.query(User).filter(User.username == username_norm).first():
        raise HTTPException(status_code=400, detail="Já existe um usuário com esse nome.")

    user = User(username=username_norm, password_hash=hash_password(payload.password), is_admin=payload.is_admin)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
