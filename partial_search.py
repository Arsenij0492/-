# partial_search.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from terms_data import get_all_terms, find_term

active_sessions = {}

def is_search_active(user_id: int) -> bool:
    return active_sessions.get(user_id, False)

def start_search_session(user_id: int):
    active_sessions[user_id] = True

def clear_search_session(user_id: int):
    active_sessions[user_id] = False

async def show_partial_search_menu(update, context, query=None):
    text = "🔤 *Поиск по части слова*\n\nВведите ЛЮБЫЕ БУКВЫ - найду ВСЕ термины, где они есть.\n\n*Пример:* «ад» → адвокат, административное право"
    
    keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)

async def handle_partial_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_query = update.message.text.lower().strip()
    
    all_terms = get_all_terms()
    found_terms = []
    
    # ТОЛЬКО вхождение букв, никакого find_term
    for term in all_terms:
        if user_query in term.lower():
            found_terms.append(term)
    
    if not found_terms:
        response = f"❌ По запросу «{user_query}» ничего не найдено."
        keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(response, reply_markup=reply_markup)
        return
    
    found_terms.sort()
    total_found = len(found_terms)
    
    # Если больше 20 - предупреждение
    if total_found > 20:
        terms_preview = "\n".join([f"• {term}" for term in found_terms[:10]])
        response = f"⚠️ *Найдено слишком много терминов ({total_found})*\n\nПримеры:\n{terms_preview}\n\n_Введите более точный запрос_"
        keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(response, parse_mode="Markdown", reply_markup=reply_markup)
        return
    
    # Если один термин - перевод
    if total_found == 1:
        term_data = find_term(found_terms[0])
        response = f"""
✅ *Найден термин по запросу «{user_query}»:*

📖 *{found_terms[0]}*
*Перевод:* `{term_data['translation']}`
⚖️ *Отрасль:* {term_data['field']}
📝 *Пример:* _{term_data['example']}_
        """
        if term_data.get('note'):
            response += f"\n💡 *Примечание:* {term_data['note']}"
    else:
        terms_list = "\n".join([f"• {term}" for term in found_terms])
        response = f"🔍 *Результаты поиска «{user_query}»:*\n\nНайдено терминов: *{total_found}*\n\n{terms_list}"
    
    keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(response, parse_mode="Markdown", reply_markup=reply_markup)

def get_handlers():
    from telegram.ext import CallbackQueryHandler
    return [
        CallbackQueryHandler(lambda u,c: None, pattern="^$"),
    ]