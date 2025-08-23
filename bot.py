import os
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes
)
from ai_dialogue import generate_options

# Global game state (per chat_id)
STATE = {}

def get_state(chat_id):
    if chat_id not in STATE:
        STATE[chat_id] = {
            "scene": "City Square",
            "mischief": 0,
            "helpful": 0,
            "history": []
        }
    return STATE[chat_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    STATE[chat_id] = {
        "scene": "City Square",
        "mischief": 0,
        "helpful": 0,
        "history": []
    }
    await update.message.reply_text(
        "🎭 Welcome to *Шапокляк’s Mischief Adventures*! 🐀\n\n"
        "You are Шапокляк, a cunning trickster.\n"
        "Type /next to begin your mischief.",
        parse_mode="Markdown"
    )

async def next_scene(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    state = get_state(chat_id)

    options = generate_options(state["scene"], state["history"])

    keyboard = [[InlineKeyboardButton(opt, callback_data=opt)] for opt in options]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"📍 Scene: {state['scene']}\n\nWhat will Шапокляк do?",
        reply_markup=reply_markup
    )

async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data
    chat_id = query.message.chat_id
    state = get_state(chat_id)

    state["history"].append(choice)

    # crude scoring: check keywords
    if any(w in choice.lower() for w in ["steal", "trick", "scare", "trash", "rat"]):
        state["mischief"] += 1
    elif any(w in choice.lower() for w in ["help", "save", "protect", "kind"]):
        state["helpful"] += 1
    else:
        state["mischief"] += 1  # default mischievous

    await query.edit_message_text(
        f"👉 You chose: {choice}\n"
        f"(Mischief: {state['mischief']} | Helpful: {state['helpful']})\n\n"
        "Type /next for the next move."
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    state = get_state(chat_id)
    await update.message.reply_text(
        f"📊 Mischief: {state['mischief']} | Helpful: {state['helpful']}\n"
        f"Current scene: {state['scene']}"
    )

async def end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    state = get_state(chat_id)

    if state["mischief"] > state["helpful"]:
        ending = "😈 Шапокляк becomes a *legendary villain*!"
    elif state["helpful"] > state["mischief"]:
        ending = "🌟 Against all odds, she becomes a *reluctant hero*."
    else:
        ending = "🌀 She remains a trickster anti-hero, feared and admired."

    await update.message.reply_text(ending, parse_mode="Markdown")

async def build_application() -> Application:
    token = os.getenv("TG_BOT_TOKEN")
    if not token:
        raise SystemExit("Set TG_BOT_TOKEN environment variable")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("next", next_scene))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("end", end))
    app.add_handler(CallbackQueryHandler(handle_choice))

    return app