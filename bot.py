# bot.py
import os
from typing import Dict, Any, List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes
)

# ChatGPT helper (make sure ai_dialogue.py is in the same folder)
from ai_dialogue import generate_options  # returns List[str]


# =========================
# Simple per-chat game state
# =========================
STATE: Dict[int, Dict[str, Any]] = {}


def get_state(chat_id: int) -> Dict[str, Any]:
    """Return the state for this chat, creating defaults as needed."""
    if chat_id not in STATE:
        STATE[chat_id] = {
            "scene": "City Square",   # starting location
            "mischief": 0,
            "helpful": 0,
            "history": []             # recent player choices for AI context
        }
    return STATE[chat_id]


def reset_state(chat_id: int) -> None:
    STATE[chat_id] = {
        "scene": "City Square",
        "mischief": 0,
        "helpful": 0,
        "history": []
    }


# =========================
# Command handlers
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start a fresh story."""
    chat_id = update.effective_chat.id
    reset_state(chat_id)
    await update.message.reply_text(
        "🎭 *Шапокляк’s Mischief Adventures* 🐀\n\n"
        "You are Шапокляк — witty, sarcastic, and troublesome.\n"
        "Type /next to begin causing (or preventing) trouble!",
        parse_mode="Markdown"
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current stats and scene."""
    chat_id = update.effective_chat.id
    s = get_state(chat_id)
    await update.message.reply_text(
        f"📊 Mischief: {s['mischief']} | Helpful: {s['helpful']}\n"
        f"📍 Scene: {s['scene']}"
    )


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Compute and send an ending based on the tally."""
    chat_id = update.effective_chat.id
    s = get_state(chat_id)

    if s["mischief"] > s["helpful"]:
        ending = "😈 Шапокляк becomes a *legendary villain*!"
    elif s["helpful"] > s["mischief"]:
        ending = "🌟 Against all odds, she becomes a *reluctant hero*."
    else:
        ending = "🌀 A perfect *trickster anti-hero* — feared and admired."

    await update.message.reply_text(ending, parse_mode="Markdown")


async def next_scene(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Ask ChatGPT for 3 short options and show them as inline buttons.
    Uses current scene + recent history for context.
    """
    chat_id = update.effective_chat.id
    s = get_state(chat_id)

    options: List[str] = generate_options(s["scene"], s["history"])

    # If options contain a single diagnostic line, show it plainly.
    if len(options) == 1 and options[0].startswith("(") and options[0].endswith(")"):
        await update.message.reply_text(options[0])
        return

    keyboard = [[InlineKeyboardButton(opt, callback_data=opt)] for opt in options]
    await update.message.reply_text(
        f"📍 Scene: {s['scene']}\nWhat will Шапокляк do?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle button press, update stats & history,
    and prompt player to /next again.
    """
    q = update.callback_query
    await q.answer()
    choice = q.data
    chat_id = q.message.chat_id
    s = get_state(chat_id)

    # Record the choice for AI context
    s["history"].append(choice)

    # Lightweight scoring by keywords (tune any time)
    lc = choice.lower()
    if any(w in lc for w in ["steal", "trick", "scare", "trash", "rat", "bite", "prank", "confuse"]):
        s["mischief"] += 1
    elif any(w in lc for w in ["help", "save", "protect", "kind", "clean", "fix", "rescue"]):
        s["helpful"] += 1
    else:
        # Neutral/unclear defaults to mischievous to fit the theme
        s["mischief"] += 1

    # (Optional) You can rotate scenes here later if you want a map/progression.

    await q.edit_message_text(
        f"👉 You chose: {choice}\n"
        f"(Mischief: {s['mischief']} | Helpful: {s['helpful']})\n\n"
        "Type /next for more mischief."
    )


# -------- Optional diagnostics --------
async def diag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick check that model & API key are visible to the app."""
    try:
        from ai_dialogue import MODEL, API_KEY  # type: ignore
        masked = (API_KEY[:6] + "..." + API_KEY[-4:]) if API_KEY else "(missing)"
        await update.message.reply_text(f"Model: {MODEL}\nOPENAI_API_KEY: {masked}")
    except Exception:
        await update.message.reply_text("Diagnostics unavailable.")


# =========================
# Application factory (for webhook server)
# =========================
async def build_application() -> Application:
    """
    Build and return a configured telegram.ext.Application.
    main.py imports this and handles webhook & server.
    """
    token = os.getenv("TG_BOT_TOKEN")
    if not token:
        raise SystemExit("Set TG_BOT_TOKEN environment variable.")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("next", next_scene))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("end", end))
    app.add_handler(CommandHandler("diag", diag))            # optional
    app.add_handler(CallbackQueryHandler(handle_choice))     # buttons

    return app