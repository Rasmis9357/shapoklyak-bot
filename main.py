# main.py
import os
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

from telegram import Update
from bot import build_application   # from your shapoklyak bot.py

app = FastAPI()
tg_app = None  # will hold the Telegram Application


@app.get("/")
def root():
    return {"status": "ok", "bot": "Shapoklyak Mischief Adventures"}


@app.post("/webhook/{secret}")
async def telegram_webhook(secret: str, request: Request):
    expected = os.getenv("WEBHOOK_SECRET")
    if not expected or secret != expected:
        return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)

    data = await request.json()
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return {"ok": True}


async def startup():
    global tg_app
    tg_app = await build_application()
    await tg_app.initialize()
    await tg_app.start()

    base_url = os.getenv("RENDER_EXTERNAL_URL") or os.getenv("WEBHOOK_BASE")
    if not base_url:
        raise RuntimeError("No base URL (RENDER_EXTERNAL_URL or WEBHOOK_BASE) found.")

    secret = os.getenv("WEBHOOK_SECRET")
    if not secret:
        raise RuntimeError("WEBHOOK_SECRET is not set in environment variables.")

    webhook_url = f"{base_url.rstrip('/')}/webhook/{secret}"
    print("Setting Telegram webhook to:", webhook_url, flush=True)
    ok = await tg_app.bot.set_webhook(url=webhook_url)
    print("Webhook set result:", ok, flush=True)


async def main():
    await startup()
    port = int(os.getenv("PORT", "10000"))
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())