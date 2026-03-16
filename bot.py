#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import sys
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Токен из переменных окружения
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    logger.error("❌ Нет TELEGRAM_TOKEN в переменных окружения")
    sys.exit(1)

# URL вашего сервиса на Render (получите после деплоя)
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")

# Создаем Flask приложение для health check
app = Flask(__name__)

# Создаем Telegram приложение
telegram_app = Application.builder().token(TOKEN).build()

# ============================================
# Обработчики команд
# ============================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        f"Я работаю на Render.com! 🚀\n\n"
        f"🎤 Отправь голосовое сообщение - я его обработаю"
    )
    logger.info(f"Пользователь {user.first_name} запустил бота")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик голосовых сообщений"""
    voice = update.message.voice
    user = update.effective_user
    
    logger.info(f"🎤 Голос от {user.first_name}: {voice.duration} сек")
    
    await update.message.reply_text(
        f"✅ Получил голосовое!\n\n"
        f"📊 Длительность: {voice.duration} сек\n"
        f"📦 Размер: {voice.file_size} байт"
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text.startswith('/'):
        return
    await update.message.reply_text(f"Вы написали: {text}")

# ============================================
# Настройка вебхука
# ============================================
async def setup_webhook():
    """Устанавливает вебхук при запуске"""
    if RENDER_URL:
        webhook_url = f"{RENDER_URL}/webhook"
        await telegram_app.bot.set_webhook(url=webhook_url)
        logger.info(f"✅ Вебхук установлен: {webhook_url}")
    else:
        logger.warning("⚠️ RENDER_EXTERNAL_URL не задан")

# ============================================
# Flask routes
# ============================================
@app.route('/')
def index():
    return "Бот работает!", 200

@app.route('/health', methods=['GET'])
def health():
    """Health check для Render"""
    return "OK", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """Принимает обновления от Telegram"""
    json_data = request.get_json()
    if json_data:
        update = Update.de_json(json_data, telegram_app.bot)
        asyncio.run(telegram_app.process_update(update))
        logger.info("✅ Получено обновление")
    return "OK", 200

# ============================================
# Запуск
# ============================================
if __name__ == "__main__":
    # Добавляем обработчики
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    # Устанавливаем вебхук
    asyncio.run(setup_webhook())
    
    # Запускаем Flask сервер
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)