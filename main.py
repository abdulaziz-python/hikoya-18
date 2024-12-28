import json
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import F
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

API_TOKEN = "7924196952:AAFO0CbRKhD23Njx9-wa2otNw9OK4lURlgI"
WEBHOOK_PATH = "/bot/"
WEBHOOK_URL = "https://8000-idx-moderator-1735212668681.cluster-blu4edcrfnajktuztkjzgyxzek.cloudworkstations.dev" + WEBHOOK_PATH

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
app = FastAPI()

ADMIN_IDS = [855424189, 7099992268]

def load_hikoyalar():
    try:
        with open("hikoyalar.json", "r", encoding="utf-8") as f:
            return json.load(f)["hikoyalar"]
    except FileNotFoundError:
        return []

def save_hikoyalar(hikoyalar):
    with open("hikoyalar.json", "w", encoding="utf-8") as f:
        json.dump({"hikoyalar": hikoyalar}, f, ensure_ascii=False, indent=4)

def get_user_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="📜 Hikoyalar")
    builder.button(text="📑 Janrlar")
    builder.button(text="🧑‍🎤 Mualliflar")
    builder.button(text="✉️ Admin bilan bogʻlanish")
    builder.button(text="🎲 Random hikoya")
    builder.button(text="🔙 Chiqish")
    return builder.as_markup(resize_keyboard=True)

def get_admin_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="➕ Hikoya qo'shish")
    builder.button(text="📋 Hikoyalar ro'yxati")
    builder.button(text="❌ Hikoyani o'chirish")
    builder.button(text="🔙 Chiqish")
    return builder.as_markup(resize_keyboard=True)

class AddStory(StatesGroup):
    waiting_for_title = State()
    waiting_for_author = State()
    waiting_for_genre = State()
    waiting_for_text = State()

class DeleteStory(StatesGroup):
    waiting_for_story_id = State()

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    if message.from_user.id in ADMIN_IDS:
        await message.reply("Assalomu alaykum, xush kelibsiz, Admin!", reply_markup=get_admin_menu())
    else:
        await message.reply("Xush kelibsiz! Tugmalardan foydalanib oʻzingizga kerakli boʻlimni tanlang. ", reply_markup=get_user_menu())

@dp.message(lambda message: message.text == "➕ Hikoya qo'shish")
async def add_story_start(message: types.Message, state: FSMContext):
    await message.reply("Yangi hikoya sarlavhasini kiriting:")
    await state.set_state(AddStory.waiting_for_title)

@dp.message(AddStory.waiting_for_title)
async def add_story_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.reply("Hikoya muallifini kiriting:")
    await state.set_state(AddStory.waiting_for_author)

@dp.message(AddStory.waiting_for_author)
async def add_story_author(message: types.Message, state: FSMContext):
    await state.update_data(author=message.text)
    await message.reply("Hikoya janrini kiriting:")
    await state.set_state(AddStory.waiting_for_genre)

@dp.message(AddStory.waiting_for_genre)
async def add_story_genre(message: types.Message, state: FSMContext):
    await state.update_data(genre=message.text)
    await message.reply("Hikoya matnini kiriting:")
    await state.set_state(AddStory.waiting_for_text)

@dp.message(AddStory.waiting_for_text)
async def add_story_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    new_story = {
        "id": len(load_hikoyalar()) + 1,
        "sarlavha": data["title"],
        "muallif": data["author"],
        "janr": data["genre"],
        "matn": message.text,
    }
    hikoyalar = load_hikoyalar()
    hikoyalar.append(new_story)
    save_hikoyalar(hikoyalar)
    await message.reply("Yangi hikoya muvaffaqiyatli qo'shildi!", reply_markup=get_admin_menu())
    await state.clear()

@dp.message(lambda message: message.text == "📋 Hikoyalar ro'yxati")
async def admin_hikoyalar_list(message: types.Message):
    hikoyalar = load_hikoyalar()
    if not hikoyalar:
        await message.reply("Hozircha hech qanday hikoya yo'q.")
        return
    javob = "Mavjud hikoyalar:\n\n"
    for hikoya in hikoyalar:
        javob += f"ID: {hikoya['id']}, Sarlavha: {hikoya['sarlavha']}, Muallif: {hikoya['muallif']}, Janr: {hikoya['janr']}\n"
    await message.reply(javob)

@dp.message(lambda message: message.text == "❌ Hikoyani o'chirish")
async def delete_story_start(message: types.Message, state: FSMContext):
    await message.reply("O'chirish uchun hikoya ID-sini kiriting:")
    await state.set_state(DeleteStory.waiting_for_story_id)

@dp.message(DeleteStory.waiting_for_story_id)
async def delete_story_id(message: types.Message, state: FSMContext):
    hikoya_id = int(message.text)
    hikoyalar = load_hikoyalar()
    hikoya = next((h for h in hikoyalar if h["id"] == hikoya_id), None)
    if hikoya:
        hikoyalar = [h for h in hikoyalar if h["id"] != hikoya_id]
        save_hikoyalar(hikoyalar)
        await message.reply(f"Hikoya ID {hikoya_id} muvaffaqiyatli o'chirildi.", reply_markup=get_admin_menu())
    else:
        await message.reply(f"Hikoya ID {hikoya_id} topilmadi.", reply_markup=get_admin_menu())
    await state.clear()

@dp.message(F.text == "📜 Hikoyalar")
async def user_hikoyalar(message: types.Message):
    hikoyalar = load_hikoyalar()
    if not hikoyalar:
        await message.reply("Hozircha hech qanday hikoya yo'q.")
    else:
        javob = "Mavjud hikoyalar:\n\n"
        for hikoya in hikoyalar:
            javob += f"ID: {hikoya['id']}, Sarlavha: {hikoya['sarlavha']}, Janr: {hikoya['janr']}\n"
        await message.reply(javob)

@dp.message(lambda message: message.text == "📑 Janrlar")
async def janrlar_list(message: types.Message):
    hikoyalar = load_hikoyalar()
    janrlar = {hikoya["janr"] for hikoya in hikoyalar}
    if not janrlar:
        await message.reply("Hozircha hech qanday janr yo'q.")
        return
    builder = ReplyKeyboardBuilder()
    for janr in janrlar:
        builder.button(text=janr)
    builder.button(text="🔙 Chiqish")
    await message.reply("Qaysi janrdagi hikoyalarni oʻqishni xohlaysiz?", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(lambda message: message.text in [hikoya['janr'] for hikoya in load_hikoyalar()])
async def hikoyalar_by_janr(message: types.Message):
    janr = message.text
    hikoyalar = load_hikoyalar()
    filtered_hikoyalar = [hikoya for hikoya in hikoyalar if hikoya['janr'] == janr]
    if not filtered_hikoyalar:
        await message.reply(f"Bu janrga oid hikoyalar mavjud emas.")
        return
    javob = f"{janr} janridagi hikoyalar:\n\n"
    for hikoya in filtered_hikoyalar:
        javob += f"ID: {hikoya['id']}, Sarlavha: {hikoya['sarlavha']}\n"
    await message.reply(javob)

@dp.message(lambda message: message.text == "🧑‍🎤 Mualliflar")
async def mualliflar_list(message: types.Message):
    hikoyalar = load_hikoyalar()
    mualliflar = {hikoya["muallif"] for hikoya in hikoyalar}
    if not mualliflar:
        await message.reply("Hozircha hech qanday mualliflar yo'q.")
        return
    builder = ReplyKeyboardBuilder()
    for muallif in mualliflar:
        builder.button(text=muallif)
    builder.button(text="🔙 Chiqish")
    await message.reply("Qaysi muallif hikoyalarini oʻqishni xohlaysiz?", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(lambda message: message.text in [hikoya['muallif'] for hikoya in load_hikoyalar()])
async def hikoyalar_by_muallif(message: types.Message):
    muallif = message.text
    hikoyalar = load_hikoyalar()
    filtered_hikoyalar = [hikoya for hikoya in hikoyalar if hikoya['muallif'] == muallif]
    if not filtered_hikoyalar:
        await message.reply(f"Bu muallifga oid hikoyalar mavjud emas.")
        return
    javob = f"{muallif} muallifining hikoyalari:\n\n"
    for hikoya in filtered_hikoyalar:
        javob += f"ID: {hikoya['id']}, Sarlavha: {hikoya['sarlavha']}\n"
    await message.reply(javob)

@dp.message(lambda message: message.text == "🎲 Random hikoya")
async def random_hikoya(message: types.Message):
    hikoyalar = load_hikoyalar()
    if not hikoyalar:
        await message.reply("Hozircha hech qanday hikoya mavjud emas.")
        return
    random_hikoya = random.choice(hikoyalar)
    javob = f"🎲 Tasodifiy hikoya:\n\n"
    javob += f"ID: {random_hikoya['id']}\nSarlavha: {random_hikoya['sarlavha']}\n\n"
    javob += f"Matn: {random_hikoya['matn']}"
    await message.reply(javob)

@dp.message(lambda message: message.text in ["📑 Janrlar", "🧑‍🎤 Mualliflar"])
async def show_random_button(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.button(text="🎲 Random hikoya")
    builder.button(text="🔙 Chiqish")
    await message.reply("Random hikoya olish uchun tugmani bosing:", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(F.text == "✉️ Admin bilan bogʻlanish")
async def user_tavsiya(message: types.Message):
    await message.reply("Admin bilan bog'lanish: @Mister_Beck")

@dp.message(F.text == "🔙 Chiqish")
async def user_chiqish(message: types.Message):
    if message.from_user.id in ADMIN_IDS:
        await message.reply("Admin paneliga qaytdingiz.", reply_markup=get_admin_menu())
    else:
        await message.reply("Asosiy menyuga qaytdingiz.", reply_markup=get_user_menu())

@dp.message(F.text.regexp(r"^\d+$"))
async def user_hikoya_according_to_id(message: types.Message):
    hikoya_id = int(message.text)
    hikoyalar = load_hikoyalar()
    hikoya = next((h for h in hikoyalar if h["id"] == hikoya_id), None)
    if hikoya:
        javob = (
            f"📖 *Hikoya*: {hikoya['sarlavha']}\n"
            f"🖊 *Muallif*: {hikoya['muallif']}\n"
            f"📚 *Janr*: {hikoya['janr']}\n\n"
            f"💬 *Matn*: {hikoya['matn']}"
        )
        await message.reply(javob, parse_mode="Markdown")
    else:
        await message.reply(f"⚠ Hikoya ID {hikoya_id} topilmadi.")

@app.post(WEBHOOK_PATH)
async def bot_webhook(update: dict):
    telegram_update = types.Update(**update)
    await dp.feed_update(bot, telegram_update)
    return {"ok": True}

@app.on_event("startup")
async def on_startup():
    webhook_info = await bot.get_webhook_info()
    if webhook_info.url != WEBHOOK_URL:
        await bot.set_webhook(url=WEBHOOK_URL)

@app.on_event("shutdown")
async def on_shutdown():
    await bot.session.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
