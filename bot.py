# bot.py
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from config import TOKEN
from terms_data import get_all_terms, get_terms_by_field, get_all_fields, find_term
from show_terms import show_terms_page, show_term_detail

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Хранилища для разных режимов поиска
exact_search_active = {}
partial_search_active = {}

def set_exact_search(user_id: int, active: bool):
    exact_search_active[user_id] = active

def is_exact_search(user_id: int) -> bool:
    return exact_search_active.get(user_id, False)

def set_partial_search(user_id: int, active: bool):
    partial_search_active[user_id] = active

def is_partial_search(user_id: int) -> bool:
    return partial_search_active.get(user_id, False)

def get_search_keyboard():
    """Кнопки для возврата к выбору поиска (на всю ширину)"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔎 Точное слово", callback_data="exact_search")],
        [InlineKeyboardButton("🔤 Часть слова", callback_data="partial_search")],
        [InlineKeyboardButton("📚 По сфере права", callback_data="search_field")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
    ])

def get_main_keyboard():
    """Главное меню (на всю ширину)"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Поиск", callback_data="menu_search")],
        [InlineKeyboardButton("📚 Словарь", callback_data="menu_dictionary")],
        [InlineKeyboardButton("ℹ️ О проекте", callback_data="menu_about")]
    ])

async def show_main_menu(update, context, query=None):
    if query:
        await query.edit_message_text(
            "👋 *Добро пожаловать в Цифровой ассистент юридического перевода!*\n\nЗдесь вы можете найти перевод юридического термина.\n\nВыберите раздел:",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
    else:
        await update.message.reply_text(
            "👋 *Добро пожаловать в Цифровой ассистент юридического перевода!*\n\nЗдесь вы можете найти перевод юридического термина.\n\nВыберите раздел:",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )

async def start(update, context):
    user_id = update.effective_user.id
    set_exact_search(user_id, False)
    set_partial_search(user_id, False)
    context.user_data.clear()
    await show_main_menu(update, context)

async def button_callback(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.effective_user.id
    
    # Меню поиска
    if data == "menu_search":
        await query.edit_message_text(
            "🔍 *Выберите тип поиска:*",
            parse_mode="Markdown",
            reply_markup=get_search_keyboard()
        )
    
    # Точный поиск
    elif data == "exact_search":
        set_exact_search(user_id, True)
        set_partial_search(user_id, False)
        text = "🔎 *Режим точного поиска*\n\nВведите термин ПОЛНОСТЬЮ.\n\n*Пример:* «адвокат» - найдет, «ад» - нет"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_search_keyboard())
    
    # Частичный поиск
    elif data == "partial_search":
        set_partial_search(user_id, True)
        set_exact_search(user_id, False)
        text = "🔤 *Режим поиска по части слова*\n\nВведите ЛЮБЫЕ БУКВЫ - найду ВСЕ термины, где они есть.\n\n*Пример:* «ад» → адвокат, административное право"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_search_keyboard())
    
    # Поиск по сфере - список сфер
    elif data == "search_field":
        fields = get_all_fields()
        keyboard = []
        for field in fields:
            keyboard.append([InlineKeyboardButton(f"⚖️ {field}", callback_data=f"field_{field}")])
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="menu_search")])
        await query.edit_message_text(
            "📚 *Выберите сферу права:*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    # Выбрана сфера - показываем термины
    elif data.startswith("field_"):
        field_name = data[6:]
        terms = get_terms_by_field(field_name)
        if terms:
            context.user_data['current_terms'] = terms
            context.user_data['current_field'] = field_name
            context.user_data['current_page'] = 0
            await show_terms_page(update, context, query, terms, field_name, from_dictionary=False)
        else:
            await query.edit_message_text(
                f"❌ В сфере «{field_name}» нет терминов.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="search_field")]])
            )
    
    # Словарь (все термины)
    elif data == "menu_dictionary":
        all_terms = get_all_terms()
        context.user_data['current_terms'] = all_terms
        context.user_data['current_field'] = f"Все термины ({len(all_terms)})"
        context.user_data['current_page'] = 0
        await show_terms_page(update, context, query, all_terms, f"Все термины ({len(all_terms)})", from_dictionary=True)
    
    # Пагинация словаря
    elif data == "next_page_dict":
        page = context.user_data.get('current_page', 0)
        context.user_data['current_page'] = page + 1
        terms = context.user_data.get('current_terms', [])
        title = context.user_data.get('current_field', "Термины")
        await show_terms_page(update, context, query, terms, title, from_dictionary=True)
    
    elif data == "prev_page_dict":
        page = context.user_data.get('current_page', 0)
        context.user_data['current_page'] = page - 1
        terms = context.user_data.get('current_terms', [])
        title = context.user_data.get('current_field', "Термины")
        await show_terms_page(update, context, query, terms, title, from_dictionary=True)
    
    # Показать детали термина из словаря
    elif data.startswith("show_term_"):
        term_name = data[10:]
        await show_term_detail(update, context, query, term_name)
    
    # Назад к списку словаря
    elif data == "back_to_dict":
        terms = context.user_data.get('current_terms', [])
        title = context.user_data.get('current_field', "Термины")
        context.user_data['current_page'] = 0
        await show_terms_page(update, context, query, terms, title, from_dictionary=True)
    
    # О проекте
    elif data == "menu_about":
        about_text = """
*ℹ️ О проекте*

🎯 *Цифровой ассистент юридического перевода*

👥 *Команда проекта:*
• Расоева Хатуна
• Калинина Полина
• Пичиц Алена
• Безуглова Александра

👨‍🏫 *Научный руководитель:* Бычкова О.Н.

📅 *Сроки:* ноябрь 2025 — май 2026
        """
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_main")]]
        await query.edit_message_text(about_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    
    # Назад в главное меню
    elif data == "back_main":
        set_exact_search(user_id, False)
        set_partial_search(user_id, False)
        context.user_data.clear()
        await show_main_menu(update, context, query)

async def handle_message(update, context):
    user_id = update.effective_user.id
    user_query = update.message.text.lower().strip()
    
    # ТОЧНЫЙ ПОИСК
    if is_exact_search(user_id):
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
            response = f"❌ Термин «{user_query}» не найден.\n\nПроверьте написание."
        
        await update.message.reply_text(response, parse_mode="Markdown", reply_markup=get_search_keyboard())
        return
    
    # ЧАСТИЧНЫЙ ПОИСК
    if is_partial_search(user_id):
        all_terms = get_all_terms()
        found_terms = []
        
        for term in all_terms:
            if user_query in term.lower():
                found_terms.append(term)
        
        if not found_terms:
            response = f"❌ По запросу «{user_query}» ничего не найдено."
            await update.message.reply_text(response, reply_markup=get_search_keyboard())
            return
        
        found_terms.sort()
        total_found = len(found_terms)
        
        if total_found > 20:
            terms_preview = "\n".join([f"• {term}" for term in found_terms[:10]])
            response = f"⚠️ *Найдено слишком много терминов ({total_found})*\n\nПримеры:\n{terms_preview}\n\n_Введите более точный запрос_"
            await update.message.reply_text(response, parse_mode="Markdown", reply_markup=get_search_keyboard())
            return
        
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
        
        await update.message.reply_text(response, parse_mode="Markdown", reply_markup=get_search_keyboard())
        return
    
    # Если не в режиме поиска
    await update.message.reply_text(
        "Нажмите /start для поиска",
        reply_markup=get_main_keyboard()
    )

async def error_handler(update, context):
    logger.error(f"Error: {context.error}")

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    
    print("Бот запущен...")
    app.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == "__main__":
    main()
