# bot.py
import os
from typing import Dict, Any, List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from ai_dialogue import generate_options  # returns List[str]

STATE: Dict[int, Dict[str, Any]] = {}

def get_state(chat_id: int) -> Dict[str, Any]:
    if chat_id not in STATE:
        STATE[chat_id] = {"scene": "City Square", "mischief": 0, "helpful": 0, "history": []}
    return STATE[chat_id]

def reset_state(chat_id: int) -> None:
    STATE[chat_id] = {"scene": "City Square", "mischief": 0, "helpful": 0, "history": []}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    reset_state(chat_id)
    await update.message.reply_text(
        "🎭 *Шапокляк’s Mischief Adventures* 🐀\n\n"
        "You are Шапокляк — witty, sarcastic, and troublesome.\n"
        "Type /next to begin causing (or preventing) trouble!",
        parse_mode="Markdown"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = get_state(update.effective_chat.id)
    await update.message.reply_text(f"📊 Mischief: {s['mischief']} | Helpful: {s['helpful']}\n📍 Scene: {s['scene']}")

async def end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = get_state(update.effective_chat.id)
    if s["mischief"] > s["helpful"]:
        ending = "😈 Шапокляк becomes a *legendary villain*!"
    elif s["helpful"] > s["mischief"]:
        ending = "🌟 Against all odds, she becomes a *reluctant hero*."
    else:
        ending = "🌀 A perfect *trickster anti-hero* — feared and admired."
    await update.message.reply_text(ending, parse_mode="Markdown")

async def next_scene(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    s = get_state(chat_id)

    options: List[str] = generate_options(s["scene"], s["history"])

    # If options contain a single diagnostic line, show it plainly and stop
    if len(options) == 1 and options[0].startswith("(") and options[0].endswith(")"):
        await update.message.reply_text(options[0])
        return

    keyboard = [[InlineKeyboardButton(opt, callback_data=opt)] for opt in options]
    await update.message.reply_text(
        f"📍 Scene: {s['scene']}\nWhat will Шапокляк do?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    choice = q.data
    chat_id = q.message.chat_id
    s = get_state(chat_id)

    s["history"].append(choice)

    lc = choice.lower()
    if any(w in lc for w in ["steal", "trick", "scare", "trash", "rat", "bite", "prank", "confuse"]):
        s["mischief"] += 1
    elif any(w in lc for w in ["help", "save", "protect", "kind", "clean", "fix", "rescue"]):
        s["helpful"] += 1
    else:
        s["mischief"] += 1

    await q.edit_message_text(
        f"👉 You chose: {choice}\n"
        f"(Mischief: {s['mischief']} | Helpful: {s['helpful']})\n\n"
        "Type /next for more mischief."
    )

# --- rock-solid diagnostics (no import from ai_dialogue) ---
async def diag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    model = os.getenv("DIALOGUE_MODEL", "gpt-4o-mini")
    key = os.getenv("OPENAI_API_KEY") or ""
    masked = f"{key[:6]}...{key[-4:]}" if len(key) >= 12 else "(missing)"
    await update.message.reply_text(f"Model: {model}\nOPENAI_API_KEY: {masked}")

async def build_application() -> Application:
    token = os.getenv("TG_BOT_TOKEN")
    if not token:
        raise SystemExit("Set TG_BOT_TOKEN environment variable.")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("next", next_scene))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("end", end))
    app.add_handler(CommandHandler("diag", diag))         # diagnostics
    app.add_handler(CallbackQueryHandler(handle_choice))  # buttons
    return app