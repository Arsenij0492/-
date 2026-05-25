# exact_search.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from terms_data import find_term

active_sessions = {}

def is_search_active(user_id: int) -> bool:
    return active_sessions.get(user_id, False)

def start_search_session(user_id: int):
    active_sessions[user_id] = True

def clear_search_session(user_id: int):
    active_sessions[user_id] = False

async def show_exact_search_menu(update, context, query=None):
    text = "🔎 *Поиск по точному слову*\n\nВведите термин ПОЛНОСТЬЮ.\n\n*Пример:* «адвокат» - найдет\n«ад» - НЕ найдет"
    
    keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)

async def handle_exact_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_query = update.message.text.lower().strip()
    
    # ТОЛЬКО прямое совпадение
    result = find_term(user_query)
    
    if result:
        response = f"""
✅ *Найден термин:*

📖 *{user_query}*
*Перевод:* `{result['translation']}`
⚖️ *Отрасль:* {result['field']}
📝 *Пример:* _{result['example']}_
        """
        if result.get('note'):
            response += f"\n💡 *Примечание:* {result['note']}"
    else:
        response = f"❌ Термин «{user_query}» не найден."
    
    keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(response, parse_mode="Markdown", reply_markup=reply_markup)

def get_handlers():
    from telegram.ext import CallbackQueryHandler, MessageHandler, filters
    return [
        CallbackQueryHandler(lambda u,c: None, pattern="^$"),  # пустой, но нужен для формата
    ]