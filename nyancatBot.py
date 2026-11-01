import asyncio
import time
import os
import sqlite3
import aiohttp

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ================== НАСТРОЙКИ ==================
BOT_TOKEN = "9202071574:AAF7kryIzZILTLlP9F_zYj2fk8X9UjjsTY0"
ADMIN_ID = 6105285460 # TELEGRAM ID
COOLDOWN_SECONDS = 30 * 60 # 30 минут
DB_NAME = "nyankets.db"
IMAGES_DIR = "nyanket_images"
# ===============================================

# папку для картинок, если ее нет
os.makedirs(IMAGES_DIR, exist_ok=True)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Хранилище кулдаунов: {user_id: timestamp}
cooldowns: dict[int, float] = {}

# ================== РАБОТА С БАЗОЙ ДАННЫХ ==================
def init_db():
    """таблица, если ее нет."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nyankets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT NOT NULL,
            description TEXT NOT NULL,
            added_by INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def add_nyanket(file_id: str, description: str, user_id: int):
    """новый нянкет в базу."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO nyankets (file_id, description, added_by) VALUES (?, ?, ?)",
        (file_id, description, user_id)
    )
    conn.commit()
    conn.close()

def get_random_nyanket():
    """Достает случайный нянкет."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT file_id, description FROM nyankets ORDER BY RANDOM() LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    return result

def get_all_nyankets():
    """Достает все нянкеты для библиотеки."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, file_id, description FROM nyankets")
    results = cursor.fetchall()
    conn.close()
    return results

# ================== ХЭНДЛЕРЫ ==================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "привет! 🐱🌈\n"
        "напиши «нян» или «нянкет» — и получишь случайного нянкета.\n"
        "⏳ кулдаун: 30 минут.\n\n"
        "📚 посмотреть всех собранных нянкетов: /library\n"
    )

@dp.message(F.text.lower().in_({"нян", "нянкет"}))
async def send_nyanket(message: Message):
    user_id = message.from_user.id
    now = time.time()

    # Проверка кулдауна
    last_used = cooldowns.get(user_id, 0)
    remaining = COOLDOWN_SECONDS - (now - last_used)

    if remaining > 0:
        minutes = int(remaining // 60)
        seconds = int(remaining % 60)
        await message.reply(
            f"⏳ подожди ещё {minutes} мин {seconds} сек перед следующей картинкой!"
        )
        return

    nyanket = get_random_nyanket()
    if not nyanket:
        await message.reply("😿 В библиотеке пока нет нянкетов, админ должен добавить их!")
        return

    file_id, description = nyanket

    # обновляем кулдаун только при успешной отправке
    cooldowns[user_id] = now
    
    await message.reply_photo(photo=file_id, caption=f"✨ {description}")

# ================== ДОБАВЛЕНИЕ КАРТИНОК (АДМИН) ==================

@dp.message(F.photo & F.caption)
async def handle_new_photo(message: Message):
    if message.from_user.id != ADMIN_ID:
        return # игнорируем фото от других пользователей

    # Берем картинку в максимальном качестве
    photo = message.photo[-1]
    description = message.caption
    
    add_nyanket(photo.file_id, description, message.from_user.id)
    
    await message.reply(
        f"✅ нянкет успешно добавлен в библиотеку!\n"
        f"Подпись: {description}"
    )

# ================== БИБЛИОТЕКА ==================
@dp.message(Command("library"))
async def cmd_library(message: Message):
    nyankets = get_all_nyankets()
    
    if not nyankets:
        await message.answer("библиотека пока пуста, добавь нянкетов!")
        return

    # Отправляем первое фото
    await send_library_page(message.chat.id, nyankets, page=0)

async def send_library_page(chat_id: int, nyankets: list, page: int):
    """Функция для отображения конкретной страницы библиотеки."""
    total_pages = len(nyankets)
    # Защита от выхода за границы (если удалить сообщения)
    page = max(0, min(page, total_pages - 1))
    
    nyanket_id, file_id, description = nyankets[page]
    
    # Создаем кнопки "Назад" и "Вперед"
    builder = InlineKeyboardBuilder()
    if page > 0:
        builder.button(text="← назад", callback_data=f"lib_{page-1}")
    builder.button(text=f"{page+1} / {total_pages}", callback_data="ignore")
    if page < total_pages - 1:
        builder.button(text="вперёд →", callback_data=f"lib_{page+1}")
    
    text = f"📚 библиотека нянкетов\n\n📝 Подпись: {description}"
    
    await bot.send_photo(
        chat_id=chat_id, 
        photo=file_id, 
        caption=text, 
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data.startswith("lib_"))
async def handle_library_navigation(callback: CallbackQuery):
    page = int(callback.data.split("_")[1])
    nyankets = get_all_nyankets()
    
    # Удаляем старое сообщение с кнопками, чтобы не засорять чат
    await callback.message.delete()
    
    # Отправляем новую страницу
    await send_library_page(callback.message.chat.id, nyankets, page)
    await callback.answer()

# ================== ЗАПУСК ==================
async def main():
    init_db()
    print("бот запущен, подождите пока он домурлычет...")
    await dp.start_polling(bot)
    import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- Мини-сайт для Render ---
class WebServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), WebServer)
    server.serve_forever()

if __name__ == "__main__":
    # Запускаем сайт в фоне, чтобы Render не ругался
    threading.Thread(target=run_web_server, daemon=True).start()
    # Запускаем самого бота
    asyncio.run(main())
    
