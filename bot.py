import asyncio
import logging
import pandas as pd
from aiogram import Bot, Dispatcher
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from twitter_parser import collect_tweets
from sentiment_model import predict_sentiment
from datetime import datetime

API_TOKEN = "7684239570:AAFqFCKUQOTVbvUgXs3zIHDbyoqBMscIu_k"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

analysis_settings = {
    "date": None,
    "tweet_count": None,
    "keyword": None,
}

class AnalyzeStates(StatesGroup):
    awaiting_keyword = State()
    awaiting_date = State()
    awaiting_tweet_count = State()

@dp.message(Command("start"))
async def start(message: Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Анализ твитов")],
        ],
        resize_keyboard=True
    )
    await message.answer(
        "Привет! Я бот для анализа твитов. Нажмите '🔍 Анализ твитов', чтобы начать.",
        reply_markup=keyboard
    )

@dp.message(lambda message: message.text == "🔍 Анализ твитов")
async def analyze(message: Message, state: FSMContext):
    await message.answer("Введите ключевое слово для анализа:")
    await state.set_state(AnalyzeStates.awaiting_keyword)

@dp.message(StateFilter(AnalyzeStates.awaiting_keyword))
async def get_keyword(message: Message, state: FSMContext):
    analysis_settings["keyword"] = message.text
    current_month = datetime.now().strftime("%Y-%m")
    await message.answer(f"Введите дату за текущий месяц ({current_month}-DD):")
    await state.set_state(AnalyzeStates.awaiting_date)

@dp.message(StateFilter(AnalyzeStates.awaiting_date))
async def get_date(message: Message, state: FSMContext):
    try:
        date = message.text
        datetime.strptime(date, "%Y-%m-%d")
        if not date.startswith(datetime.now().strftime("%Y-%m")):
            raise ValueError("Дата должна быть из текущего месяца.")
        analysis_settings["date"] = date
        await message.answer("Введите количество твитов для анализа:")
        await state.set_state(AnalyzeStates.awaiting_tweet_count)
    except ValueError as e:
        await message.answer(f"Ошибка: {str(e)}. Попробуйте снова.")

@dp.message(StateFilter(AnalyzeStates.awaiting_tweet_count))
async def get_tweet_count(message: Message, state: FSMContext):
    try:
        count = int(message.text)
        if count <= 0:
            raise ValueError("Количество твитов должно быть положительным числом.")
        analysis_settings["tweet_count"] = count
        await message.answer(f"Собираю твиты по ключевому слову '{analysis_settings['keyword']}' за {analysis_settings['date']}.")

        tweets = collect_tweets(analysis_settings["keyword"], analysis_settings["date"], analysis_settings["tweet_count"])

        if not tweets:
            await message.answer("Не удалось собрать твиты. Проверьте параметры и попробуйте снова.")
            await state.clear()
            return

        positive, negative = 0, 0
        for tweet in tweets:
            sentiment = predict_sentiment(tweet["tweet"], "./bert_sentiment_model")
            if sentiment == 1:
                positive += 1
            else:
                negative += 1

        await message.answer(
            f"Анализ завершён!\n\n"
            f"Позитивные: {positive}\n"
            f"Негативные: {negative}\n\n"
            f"Сохранено {len(tweets)} твитов в 'collected_tweets.csv'."
        )
        await state.clear()
    except ValueError as e:
        await message.answer(f"Ошибка: {str(e)}. Попробуйте снова.")

async def main():
    logging.info("Запуск бота...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
