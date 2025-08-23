# bot.py
import os
from typing import Dict, Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes
)

from ai_dialogue import generate_options  # ChatGPT helper

# ----------------------------
# Simple per-chat game state
# ----------------------------
STATE: Dict[int, Dict[str, Any]] = {}


def get_state(chat_id: int) -> Dict[str, Any]:
    """Return state dict for this chat (create default if missing)."""
    if chat_id not in STATE:
        STATE[chat_id] = {
            "scene": "City Square",
            "mischief": 0,
            "helpful": 0,
            "history": []  # recent choices/lines for AI context
        }
    return STATE[chat_id]


def reset_state(chat_id: int) -> None:
    STATE[chat_id] = {
        "scene": "City Square",
        "mischief": 0,
        "helpful": 0,
        "history": []
    }


# ----------------------------
# Commands & handlers
# ----------------------------
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
    """Show current stats."""
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
    - Uses current scene + recent history for context.
    """
    chat_id = update.effective_chat.id
    s = get_state(chat_id)

    # Generate options via OpenAI (through our helper)
    options = generate_options(s["scene"], s["history"])

    # Build inline keyboard (one button per option)
    keyboard = [[InlineKeyboardButton(opt, callback_data=opt)] for opt in options]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"📍 Scene: {s['scene']}\n"
        f"What will Шапокляк do?",
        reply_markup=reply_markup
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

    # Very light scoring by keywords (you can refine later)
    lc = choice.lower()
    if any(w in lc for w in ["steal", "trick", "scare", "trash", "rat", "bite", "prank"]):
        s["mischief"] += 1
    elif any(w in lc for w in ["help", "save", "protect", "kind", "clean", "fix"]):
        s["helpful"] += 1
    else:
        # Neutral text defaults to mischievous to fit the theme
        s["mischief"] += 1

    # Optionally, you could advance scenes here (e.g., rotate locations)
    # For now we stay in the same scene until you add a scene map.

    await q.edit_message_text(
        f"👉 You chose: {choice}\n"
        f"(Mischief: {s['mischief']} | Helpful: {s['helpful']})\n\n"
        "Type /next for more mischief."
    )


# ----------------------------
# Application factory (for webhook server)
# ----------------------------
async def build_application() -> Application:
    """
    Build and return a configured telegram.ext.Application.
    main.py imports this and takes care of webhook + server.
    """
    token = os.getenv("TG_BOT_TOKEN")
    if not token:
        raise SystemExit("Set TG_BOT_TOKEN environment variable.")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("next", next_scene))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("end", end))
    app.add_handler(CallbackQueryHandler(handle_choice))

    return app