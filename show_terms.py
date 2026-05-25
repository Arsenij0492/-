# show_terms.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from terms_data import find_term

async def show_terms_page(update, context, query, terms, title, from_dictionary=False):
    """Показывает страницу с терминами (по 15 штук)"""
    page = context.user_data.get('current_page', 0)
    TERMS_PER_PAGE = 15
    
    total_pages = (len(terms) + TERMS_PER_PAGE - 1) // TERMS_PER_PAGE
    
    if page < 0:
        page = 0
    if page >= total_pages and total_pages > 0:
        page = total_pages - 1
    context.user_data['current_page'] = page
    
    start_idx = page * TERMS_PER_PAGE
    end_idx = min(start_idx + TERMS_PER_PAGE, len(terms))
    page_terms = terms[start_idx:end_idx]
    
    # Создаем кнопки для каждого термина (на всю ширину)
    keyboard = []
    for term in page_terms:
        display_term = term if len(term) <= 35 else term[:32] + "..."
        keyboard.append([InlineKeyboardButton(f"📌 {display_term}", callback_data=f"show_term_{term}")])
    
    # Кнопки навигации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("◀️ Предыдущие", callback_data="prev_page_dict"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Следующие ▶️", callback_data="next_page_dict"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Кнопка назад
    keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"📚 *{title}*\n\n({start_idx + 1}-{end_idx} из {len(terms)})",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def show_term_detail(update, context, query, term_name):
    """Показывает детальную информацию о термине"""
    term_data = find_term(term_name)
    
    if term_data:
        response = f"""
📖 *{term_name}*

*Перевод:* `{term_data['translation']}`
⚖️ *Отрасль:* {term_data['field']}
📝 *Пример:* _{term_data['example']}_
        """
        if term_data.get('note'):
            response += f"\n💡 *Примечание:* {term_data['note']}"
        
        keyboard = [
            [InlineKeyboardButton("◀️ Назад к списку", callback_data="back_to_dict")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="back_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(response, parse_mode="Markdown", reply_markup=reply_markup)