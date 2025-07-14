import os
import logging
import aiohttp
import asyncio
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.enums import ParseMode
from aiohttp import web

load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    raise ValueError("❌ API_TOKEN не установлен! Проверь .env файл.")

RAILWAY_STATIC_URL = os.getenv("RAILWAY_STATIC_URL")
if not RAILWAY_STATIC_URL:
    raise ValueError("❌ RAILWAY_STATIC_URL не установлен! Добавь в переменные окружения.")

WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_URL = f"https://{RAILWAY_STATIC_URL}{WEBHOOK_PATH}"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

user_language = {}

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

async def fetch_currency_rates():
    async with aiohttp.ClientSession() as s:
        r = await s.get("https://api.exchangerate.host/latest?base=USD&symbols=TJS,EUR,RUB")
        data = await r.json()
    return data["rates"].get("TJS"), data["rates"].get("EUR"), data["rates"].get("RUB")

def calculate_gold_prices(oz_price, usd_tjs):
    if not oz_price or not usd_tjs:
        return None
    usd_g = oz_price / 31.1035 - 4
    tjs_g = usd_g * usd_tjs
    return {p: round(tjs_g * (float(p) / 999.9), 2) for p in ["999.9", "750", "585", "375"]}

@dp.message(F.text == "/start")
async def cmd_start(message: types.Message):
    user_language[message.from_user.id] = "ru"
    await message.answer("Добро пожаловать!", reply_markup=buttons["ru"])

@dp.message(F.text.startswith("🌐"))
async def cmd_lang(message: types.Message):
    user_id = message.from_user.id
    current_lang = user_language.get(user_id, "ru")
    new_lang_
