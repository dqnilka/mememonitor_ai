import asyncio
import logging
import pandas as pd
import matplotlib.pyplot as plt
from aiogram import Bot, Dispatcher
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from twitter_parser import collect_tweets
from sentiment_model import predict_sentiment

API_TOKEN = ""

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

analysis_settings = {
    "date": "2025-01-22",
    "tweet_count": 100,
    "results": None,
    "keyword": None,
}

class AnalyzeStates(StatesGroup):
    awaiting_keyword = State()
    awaiting_tweet_count = State()


@dp.message(Command("start"))
async def start(message: Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Анализ твитов"), KeyboardButton(text="📊 Посмотреть результаты")],
            [KeyboardButton(text="💾 Скачать отчёт"), KeyboardButton(text="⚙️ Настройки")],
        ],
        resize_keyboard=True
    )
    await message.answer(
        "Привет! Я бот для анализа твитов. Выберите, что вы хотите сделать:",
        reply_markup=keyboard
    )


@dp.message(lambda message: message.text == "🔍 Анализ твитов")
async def analyze(message: Message, state: FSMContext):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отмена")],
        ],
        resize_keyboard=True
    )
    await message.answer("Введите ключевое слово для анализа (например, $coby):", reply_markup=keyboard)
    await state.set_state(AnalyzeStates.awaiting_keyword)


@dp.message(StateFilter(AnalyzeStates.awaiting_keyword))
async def get_keyword(message: Message, state: FSMContext):
    keyword = message.text
    analysis_settings["keyword"] = keyword
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отмена")],
        ],
        resize_keyboard=True
    )
    await message.answer(f"Сколько твитов проанализировать? (по умолчанию: {analysis_settings['tweet_count']})", reply_markup=keyboard)
    await state.set_state(AnalyzeStates.awaiting_tweet_count)


@dp.message(StateFilter(AnalyzeStates.awaiting_tweet_count))
async def get_tweet_count(message: Message, state: FSMContext):
    try:
        count = int(message.text)
        analysis_settings["tweet_count"] = count
    except ValueError:
        await message.answer("Некорректное значение. Будет использовано значение по умолчанию (100).")
        analysis_settings["tweet_count"] = 100

    await message.answer("Пожалуйста, подождите. Я собираю и анализирую твиты...")
    tweets = collect_tweets(analysis_settings["keyword"], analysis_settings["date"], analysis_settings["tweet_count"])

    if not tweets:
        await message.answer("Не удалось собрать твиты. Пожалуйста, проверьте настройки или попробуйте снова.")
        await state.clear()
        return

    results = []
    positive, negative = 0, 0
    for tweet in tweets:
        sentiment = predict_sentiment(tweet["tweet"], "./bert_sentiment_model")
        if sentiment == 1:
            positive += 1
        else:
            negative += 1
        results.append({"tweet": tweet["tweet"], "sentiment": "positive" if sentiment == 1 else "negative"})

    analysis_settings["results"] = results

    total = positive + negative
    positive_pct = (positive / total) * 100
    negative_pct = (negative / total) * 100

    await message.answer(
        f"Анализ завершён!\n\n"
        f"➕ Позитивные: {positive_pct:.2f}%\n"
        f"➖ Негативные: {negative_pct:.2f}%\n\n"
        "Вы можете:\n"
        "1. 📊 Посмотреть примеры твитов.\n"
        "2. 💾 Скачать отчёт."
    )
    await state.clear()


@dp.message(lambda message: message.text == "Отмена")
async def cancel(message: Message, state: FSMContext):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Анализ твитов"), KeyboardButton(text="📊 Посмотреть результаты")],
            [KeyboardButton(text="💾 Скачать отчёт"), KeyboardButton(text="⚙️ Настройки")],
        ],
        resize_keyboard=True
    )
    await message.answer("Операция отменена.", reply_markup=keyboard)
    await state.clear()


# Запуск бота
async def main():
    logging.info("Запуск бота...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
