import os, logging, aiohttp, asyncio, requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from bs4 import BeautifulSoup

API_TOKEN = os.getenv("API_TOKEN")
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)
user_language = {}
buttons = {
    "ru": ReplyKeyboardMarkup(resize_keyboard=True).add(
        KeyboardButton("📈 Золото"), KeyboardButton("💱 Курсы валют"), KeyboardButton("🌐 Сменить язык")
    ),
    "tj": ReplyKeyboardMarkup(resize_keyboard=True).add(
        KeyboardButton("📈 Нархи тилло"), KeyboardButton("💱 Қурби асъор"), KeyboardButton("🌐 Забонро иваз кун")
    ),
}

def get_kitco_gold_price():
    try:
        resp = requests.get("https://www.kitco.com/gold-price-today-usa/", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        tag = soup.find("div", class_="price")
        if tag:
            text = tag.get_text().strip().replace("$","").replace(",","")
            return float(text)
    except:
        return None

async def fetch_currency_rates():
    async with aiohttp.ClientSession() as s:
        r = await s.get("https://api.exchangerate.host/latest?base=USD&symbols=TJS,EUR,RUB")
        data = await r.json()
    return data["rates"].get("TJS"), data["rates"].get("EUR"), data["rates"].get("RUB")

def calculate_gold_prices(oz_price, usd_tjs):
    if not oz_price or not usd_tjs: return None
    usd_g = oz_price/31.1035 - 4
    tjs_g = usd_g * usd_tjs
    return {p: round(tjs_g * (float(p)/999.9),2) for p in ["999.9","750","585","375"]}

@dp.message_handler(commands=["start"])
async def cmd_start(m: types.Message):
    user_language[m.from_user.id] = "ru"
    await m.answer("Добро пожаловать!", reply_markup=buttons["ru"])

@dp.message_handler(lambda msg: msg.text.startswith("🌐"))
async def cmd_lang(m: types.Message):
    u = m.from_user.id
    lang = "tj" if user_language.get(u,"ru")=="ru" else "ru"
    user_language[u] = lang
    await m.answer("Язык переключен." if lang=="ru" else "Забон иваз шуд.", reply_markup=buttons[lang])

@dp.message_handler(lambda msg: msg.text in ["📈 Золото","📈 Нархи тилло"])
async def cmd_gold(m: types.Message):
    lang = user_language.get(m.from_user.id,"ru")
    oz = await asyncio.to_thread(get_kitco_gold_price)
    usd_tjs, eur, rub = await fetch_currency_rates()
    prices = calculate_gold_prices(oz, usd_tjs)
    if not prices:
        await m.answer("⚠️ Ошибка данных" if lang=="ru" else "⚠️ Хато дар маълумот")
        return
    tpl = {"ru":"💰 Цена на золото:","tj":"💰 Нархи тилло:"}
    text = tpl[lang] + "\n\n"+ "\n".join([f"{p} — {prices[p]} сомонӣ" for p in prices])
    text += f"\n\nБиржевая цена: ${oz}\nКурс USD: {round(usd_tjs,2)} TJS"
    await m.answer(text)

@dp.message_handler(lambda msg: msg.text in ["💱 Курсы валют","💱 Қурби асъор"])
async def cmd_cur(m: types.Message):
    lang = user_language.get(m.from_user.id,"ru")
    usd_tjs, eur, rub = await fetch_currency_rates()
    tpl = {
        "ru": f"💱 USD→TJS: {round(usd_tjs,2)}\nEUR→TJS: {round(usd_tjs*eur,2)}\nRUB→TJS: {round(usd_tjs*rub,2)}",
        "tj": f"💱 Доллар→сомонӣ: {round(usd_tjs,2)}\nЕвро→сомонӣ: {round(usd_tjs*eur,2)}\nРубл→сомонӣ: {round(usd_tjs*rub,2)}"
    }
    await m.answer(tpl[lang])

if __name__=="__main__":
    executor.start_polling(dp, skip_updates=True)
