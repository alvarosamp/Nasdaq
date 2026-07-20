from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import (
    clear_failed_attempts,
    get_csrf_token,
    hash_password,
    is_locked_out,
    register_failed_attempt,
    require_admin,
    verify_csrf,
    verify_password,
)
from app.db import get_db
from app.models import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/login")
def login_page(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse(
        request, "login.html", {"csrf_token": get_csrf_token(request), "error": None}
    )


@router.post("/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
):
    if not verify_csrf(request, csrf_token):
        return templates.TemplateResponse(
            request,
            "login.html",
            {"csrf_token": get_csrf_token(request), "error": "Sessão expirada, tente novamente."},
            status_code=400,
        )

    username_norm = username.strip().lower()

    if is_locked_out(username_norm):
        return templates.TemplateResponse(
            request,
            "login.html",
            {
                "csrf_token": get_csrf_token(request),
                "error": "Muitas tentativas incorretas. Aguarde alguns minutos e tente de novo.",
            },
            status_code=429,
        )

    user = db.query(User).filter(User.username == username_norm).first()
    if user is None or not verify_password(password, user.password_hash):
        register_failed_attempt(username_norm)
        return templates.TemplateResponse(
            request,
            "login.html",
            {"csrf_token": get_csrf_token(request), "error": "Usuário ou senha inválidos."},
            status_code=401,
        )

    clear_failed_attempts(username_norm)
    request.session["user_id"] = user.id
    return RedirectResponse("/", status_code=302)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)


@router.get("/cadastro")
def cadastro_page(request: Request, db: Session = Depends(get_db)):
    if request.session.get("user_id"):
        return RedirectResponse("/", status_code=302)
    has_users = db.query(User).count() > 0
    return templates.TemplateResponse(
        request,
        "cadastro.html",
        {"csrf_token": get_csrf_token(request), "error": None, "closed": has_users},
    )


@router.post("/cadastro")
def cadastro_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
):
    has_users = db.query(User).count() > 0
    if has_users:
        return templates.TemplateResponse(
            request,
            "cadastro.html",
            {"csrf_token": get_csrf_token(request), "error": None, "closed": True},
            status_code=403,
        )

    if not verify_csrf(request, csrf_token):
        return templates.TemplateResponse(
            request,
            "cadastro.html",
            {"csrf_token": get_csrf_token(request), "error": "Sessão expirada, tente novamente.", "closed": False},
            status_code=400,
        )

    username_norm = username.strip().lower()
    error = None
    if len(username_norm) < 3:
        error = "Usuário precisa ter pelo menos 3 caracteres."
    elif len(password) < 8:
        error = "Senha precisa ter pelo menos 8 caracteres."
    elif password != password_confirm:
        error = "As senhas não coincidem."

    if error:
        return templates.TemplateResponse(
            request,
            "cadastro.html",
            {"csrf_token": get_csrf_token(request), "error": error, "closed": False},
            status_code=400,
        )

    # Re-checa dentro da mesma transação pra evitar corrida entre dois cadastros simultâneos
    # criando dois admins (ou um segundo usuário) no exato mesmo instante.
    if db.query(User).count() > 0:
        return templates.TemplateResponse(
            request,
            "cadastro.html",
            {"csrf_token": get_csrf_token(request), "error": None, "closed": True},
            status_code=403,
        )

    user = User(username=username_norm, password_hash=hash_password(password), is_admin=True)
    db.add(user)
    db.commit()
    db.refresh(user)

    request.session["user_id"] = user.id
    return RedirectResponse("/", status_code=302)


@router.get("/usuarios")
def usuarios_page(request: Request, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.created_at).all()
    return templates.TemplateResponse(
        request, "usuarios.html", {"users": users, "csrf_token": get_csrf_token(request), "error": None}
    )


@router.post("/usuarios")
def usuarios_create(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    is_admin: bool = Form(False),
    csrf_token: str = Form(...),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    users = db.query(User).order_by(User.created_at).all()

    if not verify_csrf(request, csrf_token):
        return templates.TemplateResponse(
            request,
            "usuarios.html",
            {"users": users, "csrf_token": get_csrf_token(request), "error": "Sessão expirada, tente novamente."},
            status_code=400,
        )

    username_norm = username.strip().lower()
    error = None
    if len(username_norm) < 3:
        error = "Usuário precisa ter pelo menos 3 caracteres."
    elif len(password) < 8:
        error = "Senha precisa ter pelo menos 8 caracteres."
    elif db.query(User).filter(User.username == username_norm).first():
        error = "Já existe um usuário com esse nome."

    if error:
        return templates.TemplateResponse(
            request,
            "usuarios.html",
            {"users": users, "csrf_token": get_csrf_token(request), "error": error},
            status_code=400,
        )

    new_user = User(username=username_norm, password_hash=hash_password(password), is_admin=is_admin)
    db.add(new_user)
    db.commit()

    return RedirectResponse("/usuarios", status_code=302)
