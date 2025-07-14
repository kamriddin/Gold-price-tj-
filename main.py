import os
import logging
import aiohttp
import asyncio
import requests
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.enums import ParseMode

# Получаем токен из переменной окружения
API_TOKEN = os.getenv("API_TOKEN")

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Храним язык пользователя
user_language = {}

# Клавиатуры
buttons = {
    "ru": ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📈 Золото"), KeyboardButton(text="💱 Курсы валют")],
            [KeyboardButton(text="🌐 Сменить язык")]
        ],
        resize_keyboard=True
    ),
    "tj": ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📈 Нархи тилло"), KeyboardButton(text="💱 Қурби асъор")],
            [KeyboardButton(text="🌐 Забонро иваз кун")]
        ],
        resize_keyboard=True
    )
}

# Функция для получения цены золота с Kitco
def get_kitco_gold_price():
    try:
        resp = requests.get("https://www.kitco.com/gold-price-today-usa/", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        tag = soup.find("div", class_="price")
        if tag:
            text = tag.get_text().strip().replace("$", "").replace(",", "")
            return float(text)
    except:
        return None

# Получаем курс валют
async def fetch_currency_rates():
    async with aiohttp.ClientSession() as s:
        r = await s.get("https://api.exchangerate.host/latest?base=USD&symbols=TJS,EUR,RUB")
        data = await r.json()
    return data["rates"].get("TJS"), data["rates"].get("EUR"), data["rates"].get("RUB")

# Переводим цену золота в сомони
def calculate_gold_prices(oz_price, usd_tjs):
    if not oz_price or not usd_tjs:
        return None
    usd_g = oz_price / 31.1035 - 4
    tjs_g = usd_g * usd_tjs
    return {p: round(tjs_g * (float(p) / 999.9), 2) for p in ["999.9", "750", "585", "375"]}

# Команда /start
@dp.message(F.text == "/start")
async def cmd_start(message: types.Message):
    user_language[message.from_user.id] = "ru"
    await message.answer("Добро пожаловать!", reply_markup=buttons["ru"])

# Смена языка
@dp.message(F.text.startswith("🌐"))
async def cmd_lang(message: types.Message):
    user_id = message.from_user.id
    current_lang = user_language.get(user_id, "ru")
    new_lang = "tj" if current_lang == "ru" else "ru"
    user_language[user_id] = new_lang
    await message.answer("Язык переключен." if new_lang == "ru" else "Забон иваз шуд.", reply_markup=buttons[new_lang])

# Золото
@dp.message(F.text.in_(["📈 Золото", "📈 Нархи тилло"]))
async def cmd_gold(message: types.Message):
    lang = user_language.get(message.from_user.id, "ru")
    oz_price = await asyncio.to_thread(get_kitco_gold_price)
    usd_tjs, eur, rub = await fetch_currency_rates()
    prices = calculate_gold_prices(oz_price, usd_tjs)
    if not prices:
        await message.answer("⚠️ Ошибка данных" if lang == "ru" else "⚠️ Хато дар маълумот")
        return

    header = "💰 Цена на золото:" if lang == "ru" else "💰 Нархи тилло:"
    text = header + "\n\n" + "\n".join([f"{k} — {v} сомонӣ" for k, v in prices.items()])
    text += f"\n\nБиржевая цена: ${oz_price}\nКурс USD: {round(usd_tjs, 2)} TJS"
    await message.answer(text)

# Курсы валют
@dp.message(F.text.in_(["💱 Курсы валют", "💱 Қурби асъор"]))
async def cmd_currency(message: types.Message):
    lang = user_language.get(message.from_user.id, "ru")
    usd_tjs, eur, rub = await fetch_currency_rates()

    if lang == "ru":
        text = (
            f"💱 USD→TJS: {round(usd_tjs, 2)}\n"
            f"EUR→TJS: {round(usd_tjs * eur, 2)}\n"
            f"RUB→TJS: {round(usd_tjs * rub, 2)}"
        )
    else:
        text = (...
)

            f"💱 Доллар→сомонӣ: {round(usd_tjs, 2)}\n"
            f"Евро→сомонӣ: {round(usd_tjs * eur, 2)}\n"
