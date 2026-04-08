import asyncio
import logging
import aiohttp
from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, \
    KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from src.config import settings

BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN
API_URL = "http://api:8000"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
router = Router()
logger = logging.getLogger(__name__)


# --- МАШИНЫ СОСТОЯНИЙ ---
class AddProduct(StatesGroup):
    waiting_for_url = State()
    waiting_for_name = State()
    waiting_for_price = State()


class EditPrice(StatesGroup):
    waiting_for_new_price = State()


# --- КЛАВИАТУРЫ ---
main_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить новый товар")],
        [KeyboardButton(text="📋 Просмотреть все товары")],
        [KeyboardButton(text="✏️ Изменить цену"), KeyboardButton(text="❌ Удалить товар")]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выбери действие в меню 👇"
)

# Клавиатура отмены (появляется во время ввода данных)
cancel_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Отмена")]],
    resize_keyboard=True
)


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
async def get_user_products(user_id: int):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/products/user/{user_id}") as resp:
            if resp.status == 200:
                return await resp.json()
    return []


# ==========================================
# ГЛОБАЛЬНАЯ ОТМЕНА
# ==========================================
@router.message(F.text == "❌ Отмена")
async def cancel_handler(message: Message, state: FSMContext):
    """Сбрасывает любое состояние и возвращает в главное меню"""
    await state.clear()
    await message.answer("Действие отменено. Возвращаюсь в главное меню 🏠", reply_markup=main_menu_kb)


# ==========================================
# ОПЛАТА И PREMIUM
# ==========================================
@router.callback_query(F.data == "buy_premium")
async def mock_buy_premium(callback: CallbackQuery):
    await callback.answer("⏳ Подключение платежной системы...", show_alert=False)

    # В будущем здесь будет генерация инвойса Telegram Stars или YKassa
    await callback.message.answer(
        "💳 <b>Интеграция кассы</b>\n\n"
        "Здесь мы подключим реальную платежную систему. "
        "Когда оплата пройдет успешно, бот запишет статус 'Premium' в базу данных, "
        "и лимиты будут сняты!\n\n"
        "<i>(Функционал в разработке 🛠)</i>",
        reply_markup=main_menu_kb
    )


@router.callback_query(F.data == "cancel_action")
async def cancel_inline_handler(callback: CallbackQuery, state: FSMContext):
    """Скрывает inline-меню при нажатии на Отмену"""
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.answer("Отменено")


# ==========================================
# СТАРТ
# ==========================================
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Привет! Я WatchDog — твой личный трекер цен.\n\nИспользуй меню внизу для управления своими товарами!",
        reply_markup=main_menu_kb)


# ==========================================
# ДОБАВЛЕНИЕ ТОВАРА (С проверкой дубликатов)
# ==========================================
@router.message(F.text == "➕ Добавить новый товар")
async def btn_add_product(message: Message, state: FSMContext):
    await state.set_state(AddProduct.waiting_for_url)
    # Выводим кнопку Отмена вместо главного меню
    await message.answer("🔗 Отправь мне ссылку на товар (начинается с http:// или https://):",
                         reply_markup=cancel_kb)  # noqa


@router.message(AddProduct.waiting_for_url, F.text.startswith("http"))
async def process_url(message: Message, state: FSMContext):
    url = message.text.strip()

    # 1. ПРОВЕРКА НА ДУБЛИКАТ ССЫЛКИ
    user_products = await get_user_products(message.from_user.id)
    if any(p['url'] == url for p in user_products):
        await message.answer("⚠️ <b>Ты уже следишь за этим товаром!</b>\nОтправь другую ссылку или нажми «Отмена».")
        return

    msg = await message.answer("⏳ Проверяю сайт...")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(f"{API_URL}/check-url/", json={"url": url}) as resp:
                result = await resp.json()
                if result.get("is_supported"):
                    await state.update_data(url=url, last_price=result.get("price", 0))
                    await state.set_state(AddProduct.waiting_for_name)
                    await msg.edit_text(
                        f"{result['message']}\n\n📝 <b>Придумай уникальное название:</b>\n(Например: Кроссовки Nike)")
                else:
                    await msg.edit_text(result.get("message", "❌ Ошибка проверки."))
                    await state.clear()
                    await message.answer("Возвращаюсь в меню.", reply_markup=main_menu_kb)
        except Exception as e:
            logger.error(f"Ошибка API: {e}")
            await msg.edit_text("❌ Сервис недоступен.")
            await state.clear()
            await message.answer("Возвращаюсь в меню.", reply_markup=main_menu_kb)


@router.message(AddProduct.waiting_for_name, F.text)
async def process_name(message: Message, state: FSMContext):
    name = message.text.strip()

    # 2. ПРОВЕРКА НА ДУБЛИКАТ ИМЕНИ (сравниваем в нижнем регистре, чтобы "Nike" и "nike" считались одинаковыми)
    user_products = await get_user_products(message.from_user.id)
    if any(p['name'].lower() == name.lower() for p in user_products):
        await message.answer(f"⚠️ Товар с именем <b>{name}</b> уже есть!\nПридумай другое название:")
        return

    await state.update_data(name=name)
    await state.set_state(AddProduct.waiting_for_price)
    await message.answer("🎯 Отличное название! <b>Какую желаемую цену ждем?</b> (напиши число)")


@router.message(AddProduct.waiting_for_price, F.text)
async def process_price(message: Message, state: FSMContext):
    try:
        target_price = float(message.text.replace(",", ".").replace(" ", ""))
    except ValueError:
        await message.answer("⚠️ Напиши просто число.")
        return

    data = await state.get_data()
    payload = {
        "name": data["name"],
        "url": data["url"],
        "target_price": target_price,
        "last_price": data["last_price"],
        "user_telegram_id": message.from_user.id
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_URL}/products/", json=payload) as resp:
            if resp.status == 200:
                await message.answer("✅ Товар успешно добавлен в трекер!", reply_markup=main_menu_kb)

            # --- ЛОВИМ ОШИБКУ ЛИМИТА ---
            elif resp.status == 403:
                error_data = await resp.json()
                if error_data.get("detail") == "LIMIT_REACHED":
                    # Рисуем продающую кнопку
                    kb = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="💎 Оформить Premium", callback_data="buy_premium")]
                    ])
                    await message.answer(
                        "🛑 <b>Лимит исчерпан!</b>\n\n"
                        "В базовой версии можно отслеживать не более 3-х товаров одновременно.\n\n"
                        "💎 <b>Что дает Premium-подписка?</b>\n"
                        "• Безлимитное количество товаров\n"
                        "• Приоритетная проверка цен\n"
                        "• Графики изменения стоимости\n\n"
                        "<i>Снимите ограничения прямо сейчас!</i> 👇",
                        reply_markup=kb
                    )
            else:
                await message.answer("❌ Ошибка сохранения.", reply_markup=main_menu_kb)

    await state.clear()


# ==========================================
# ПРОСМОТР ТОВАРОВ
# ==========================================
@router.message(F.text == "📋 Просмотреть все товары")
async def btn_list(message: Message, state: FSMContext):
    await state.clear()
    products = await get_user_products(message.from_user.id)

    if not products:
        await message.answer("📭 Твой список отслеживания пуст.")
        return

    text = "📋 <b>Твои товары:</b>\n\n"
    for i, p in enumerate(products, 1):
        status = "🟢" if p.get('is_active') else "🔴"
        text += f"{status} <b>{i}. {p['name']}</b>\n"
        text += f"   💰 Текущая: {p['last_price']} | 🎯 Цель: {p['target_price']}\n"
        text += f"   🔗 <a href='{p['url']}'>Ссылка на магазин</a>\n\n"

    await message.answer(text, disable_web_page_preview=True)


# ==========================================
# УДАЛЕНИЕ ТОВАРОВ
# ==========================================
@router.message(F.text == "❌ Удалить товар")
async def btn_delete_menu(message: Message, state: FSMContext):
    await state.clear()
    products = await get_user_products(message.from_user.id)

    if not products:
        await message.answer("📭 У тебя пока нет товаров для удаления.")
        return

    buttons = [[InlineKeyboardButton(text=f"🗑 {p['name']}", callback_data=f"del_{p['id']}")] for p in products]
    # Добавляем кнопку отмены в самый низ списка
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer("❌ <b>Выбери товар, который хочешь удалить:</b>", reply_markup=kb)


@router.callback_query(F.data.startswith("del_"))
async def execute_delete(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[1])

    async with aiohttp.ClientSession() as session:
        async with session.delete(f"{API_URL}/products/{product_id}") as resp:
            if resp.status == 200:
                deleted_product = await resp.json()
                product_name = deleted_product.get('name', 'Без названия')
                await callback.message.answer(f"🗑 Товар <b>{product_name}</b> удален из списка отслеживаемых.")
            else:
                await callback.answer("❌ Не удалось удалить товар.", show_alert=True)

    try:
        await callback.message.delete()
    except Exception:
        pass

    await callback.answer()


# ==========================================
# ИЗМЕНЕНИЕ ЦЕНЫ
# ==========================================
@router.message(F.text == "✏️ Изменить цену")
async def btn_edit_menu(message: Message, state: FSMContext):
    await state.clear()
    products = await get_user_products(message.from_user.id)

    if not products:
        await message.answer("📭 У тебя пока нет товаров.")
        return

    buttons = [[InlineKeyboardButton(text=f"✏️ {p['name']}", callback_data=f"edit_{p['id']}")] for p in products]
    # Добавляем кнопку отмены
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer("📝 <b>Выбери товар для изменения цены:</b>", reply_markup=kb)


@router.callback_query(F.data.startswith("edit_"))
async def execute_edit(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[1])
    products = await get_user_products(callback.from_user.id)

    target_product = next((p for p in products if p['id'] == product_id), None)
    if not target_product:
        await callback.answer("Товар не найден", show_alert=True)
        return

    await state.update_data(edit_product_id=product_id)
    await state.set_state(EditPrice.waiting_for_new_price)

    # Меняем сообщение, но оставляем inline кнопку отмены под ним
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")]])
    await callback.message.edit_text(
        f"✏️ Товар: <b>{target_product['name']}</b>\n"
        f"Текущая цель: {target_product['target_price']}\n\n"
        f"👇 Отправь мне новую желаемую цену:",
        reply_markup=kb
    )


@router.message(EditPrice.waiting_for_new_price, F.text)
async def process_new_price(message: Message, state: FSMContext):
    try:
        new_price = float(message.text.replace(",", ".").replace(" ", ""))
    except ValueError:
        await message.answer("⚠️ Напиши просто число.")
        return

    data = await state.get_data()
    async with aiohttp.ClientSession() as session:
        await session.patch(f"{API_URL}/products/{data['edit_product_id']}/price", json={"target_price": new_price})

    await state.clear()
    # Возвращаем главное меню после успешного ввода
    await message.answer("✅ Желаемая цена успешно обновлена!", reply_markup=main_menu_kb)


async def main():
    logging.basicConfig(level=logging.INFO)
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())