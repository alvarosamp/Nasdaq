from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.auth import RedirectToLogin
from app.config import settings
from app.db import init_db
from app.routers import api, assistant, auth, dashboard, positions, watchlist
from app.scheduler import build_scheduler
from app.telegram_bot import build_application

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    telegram_app = build_application()
    if telegram_app is not None:
        await telegram_app.initialize()
        await telegram_app.start()
        await telegram_app.updater.start_polling()
        logger.info("Bot do Telegram iniciado.")
    else:
        logger.warning("Rodando sem bot do Telegram (TELEGRAM_BOT_TOKEN ausente).")

    scheduler = build_scheduler(telegram_app)
    scheduler.start()
    logger.info("Scheduler iniciado.")

    app.state.telegram_app = telegram_app
    app.state.scheduler = scheduler

    yield

    scheduler.shutdown(wait=False)
    if telegram_app is not None:
        await telegram_app.updater.stop()
        await telegram_app.stop()
        await telegram_app.shutdown()
    logger.info("Encerrado.")


app = FastAPI(title="Monitor NASDAQ", lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie="nasdaq_session",
    same_site="lax",
    https_only=settings.session_cookie_secure,
)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.exception_handler(RedirectToLogin)
def redirect_to_login_handler(request: Request, exc: RedirectToLogin):
    return RedirectResponse(f"/login?next={exc.next_path}", status_code=302)


app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(watchlist.router)
app.include_router(positions.router)
app.include_router(assistant.router)
app.include_router(api.router)


@app.get("/health")
def health():
    return {"status": "ok"}
