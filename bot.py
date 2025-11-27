from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import TELEGRAM_BOT_TOKEN
from sheets import get_unsent_feedbacks, update_feedback_reply  # ✅ Добавлен импорт

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

class FeedbackNavigation(StatesGroup):
    waiting_for_category = State()
    waiting_for_product = State()
    waiting_for_rating = State()
    waiting_for_reply = State()

def get_main_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Выбрать категорию")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

def get_exit_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Выйти в меню")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await show_main_menu(message)

async def show_main_menu(message: types.Message):
    feedbacks = get_unsent_feedbacks()
    count = len(feedbacks)
    last_update = "27.11.2025"

    text = (
        f"📊 Актуально: {count} неотвеченных отзывов\n"
        f"📅 Последнее обновление: {last_update}\n\n"
        "Нажмите 'Выбрать категорию', чтобы начать."
    )
    await message.answer(text, reply_markup=get_main_menu_keyboard())

@dp.message(lambda m: m.text == "Выбрать категорию")
async def start_selection(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Выберите категорию:", reply_markup=get_exit_menu_keyboard())

    feedbacks = get_unsent_feedbacks()
    categories = list(set(fb['4'] for fb in feedbacks if fb['4']))
    categories.sort()

    text = "\n".join(f"{i} — {cat}" for i, cat in enumerate(categories))
    await message.answer(text)
    await state.set_state(FeedbackNavigation.waiting_for_category)
    await state.update_data(categories=categories)

@dp.message(FeedbackNavigation.waiting_for_category)
async def process_category(message: types.Message, state: FSMContext):
    if message.text == "Выйти в меню":
        await show_main_menu(message)
        await state.clear()
        return

    try:
        index = int(message.text)
    except ValueError:
        await message.answer("Введите число.")
        return

    data = await state.get_data()
    categories = data['categories']

    if index < 0 or index >= len(categories):
        await message.answer("Неверный номер.")
        return

    selected_category = categories[index]

    feedbacks = get_unsent_feedbacks()
    products = list(set(fb['3'] for fb in feedbacks if fb['4'] == selected_category))
    products.sort()

    text = "\n".join(f"{i} — {prod}" for i, prod in enumerate(products))
    await message.answer(text, reply_markup=get_exit_menu_keyboard())
    await state.update_data(products=products, selected_category=selected_category)
    await state.set_state(FeedbackNavigation.waiting_for_product)

@dp.message(FeedbackNavigation.waiting_for_product)
async def process_product(message: types.Message, state: FSMContext):
    if message.text == "Выйти в меню":
        await show_main_menu(message)
        await state.clear()
        return

    try:
        index = int(message.text)
    except ValueError:
        await message.answer("Введите число.")
        return

    data = await state.get_data()
    products = data['products']

    if index < 0 or index >= len(products):
        await message.answer("Неверный номер.")
        return

    selected_product = products[index]

    feedbacks = get_unsent_feedbacks()
    ratings = list(set(str(fb['5']) for fb in feedbacks
                      if fb['4'] == data['selected_category'] and fb['3'] == selected_product))
    ratings.sort(key=int)

    text = "\n".join(ratings)
    await message.answer(text, reply_markup=get_exit_menu_keyboard())
    await state.update_data(selected_product=selected_product, ratings=ratings)
    await state.set_state(FeedbackNavigation.waiting_for_rating)

@dp.message(FeedbackNavigation.waiting_for_rating)
async def process_rating(message: types.Message, state: FSMContext):
    if message.text == "Выйти в меню":
        await show_main_menu(message)
        await state.clear()
        return

    rating = message.text.strip()

    data = await state.get_data()
    ratings = data['ratings']

    if rating not in ratings:
        await message.answer("Неверная оценка.")
        return

    feedbacks = get_unsent_feedbacks()
    filtered = [fb for fb in feedbacks
                if fb['4'] == data['selected_category']
                and fb['3'] == data['selected_product']
                and str(fb['5']) == rating]

    print(f"Найдено {len(filtered)} отзывов для категории '{data['selected_category']}', товара '{data['selected_product']}', оценки '{rating}'")

    if len(filtered) == 0:
        await message.answer("Нет отзывов с такой оценкой.")
        await show_main_menu(message)
        await state.clear()
        return

    for fb in filtered:
        text_content = fb['6'] if fb['6'] else "Без текста"
        text = f"⭐️ {fb['5']}/5\n\n{text_content}"
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="Ответить", callback_data=f"reply_{fb['1']}"),
                types.InlineKeyboardButton(text="Сгенерировать", callback_data=f"generate_{fb['1']}")
            ]
        ])
        await message.answer(text, reply_markup=keyboard)

    await state.clear()

@dp.callback_query(lambda c: c.data.startswith("reply_"))
async def handle_reply_callback(callback_query: types.CallbackQuery, state: FSMContext):
    feedback_id = callback_query.data.split("_")[1]
    await state.update_data(feedback_id=feedback_id)
    await state.set_state(FeedbackNavigation.waiting_for_reply)
    await callback_query.message.answer("Пожалуйста, напишите ваш ответ:")
    await callback_query.answer()

@dp.callback_query(lambda c: c.data.startswith("generate_"))
async def handle_generate_callback(callback_query: types.CallbackQuery):
    feedback_id = callback_query.data.split("_")[1]
    # Сохраняем в таблицу: aiReply = 1
    update_feedback_reply(feedback_id, ai_reply="1")

    await callback_query.message.answer(f"✅ Сгенерированный ответ сохранён!")
    await callback_query.answer()

@dp.message(FeedbackNavigation.waiting_for_reply)
async def handle_user_reply(message: types.Message, state: FSMContext):
    user_reply = message.text
    data = await state.get_data()
    feedback_id = data['feedback_id']

    # Сохраняем ответ в Google Sheets
    update_feedback_reply(feedback_id, manual_reply=user_reply)

    await message.answer("✅ Ответ сохранён!")
    await show_main_menu(message)
    await state.clear()

if __name__ == "__main__":
    dp.run_polling(bot)