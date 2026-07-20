"""Helper script: run this once to discover your Telegram chat_id.

Usage:
  1. Set TELEGRAM_BOT_TOKEN in your .env (or export it as an env var).
  2. Open a chat with your bot on Telegram and send any message (e.g. /start).
  3. Run: python get_chat_id.py
"""
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

token = os.environ.get("TELEGRAM_BOT_TOKEN")
if not token:
    raise SystemExit("Defina TELEGRAM_BOT_TOKEN no .env antes de rodar este script.")

resp = httpx.get(f"https://api.telegram.org/bot{token}/getUpdates").json()
results = resp.get("result", [])
if not results:
    print("Nenhuma mensagem encontrada. Envie uma mensagem para o bot no Telegram e rode de novo.")
else:
    seen = set()
    for update in results:
        message = update.get("message") or update.get("channel_post")
        if not message:
            continue
        chat = message["chat"]
        if chat["id"] in seen:
            continue
        seen.add(chat["id"])
        print(f"chat_id={chat['id']}  nome={chat.get('first_name') or chat.get('title')}")
