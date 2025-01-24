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


API_TOKEN = "7943152874:AAEblbvPHqmZH_Uj0gxL-04KkJx3k3kGq-g"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Определение состояний
class AnalyzeStates(StatesGroup):
    awaiting_keyword = State()
    awaiting_date = State()


@dp.message(Command("start"))
async def start(message: Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Анализ твитов"), KeyboardButton(text="📊 Посмотреть результаты")],
        ],
        resize_keyboard=True
    )
    await message.answer(
        "Привет! Я бот для анализа твитов. Выберите действие:",
        reply_markup=keyboard
    )


@dp.message(lambda message: message.text == "🔍 Анализ твитов")
async def analyze(message: Message, state: FSMContext):
    await message.answer("Введите ключевое слово для анализа:")
    await state.set_state(AnalyzeStates.awaiting_keyword)


@dp.message(StateFilter(AnalyzeStates.awaiting_keyword))
async def get_keyword(message: Message, state: FSMContext):
    keyword = message.text
    await state.update_data(keyword=keyword)
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
        await state.update_data(date=date)

        data = await state.get_data()
        keyword = data["keyword"]

        await message.answer(f"Собираю твиты по ключевому слову '{keyword}' за {date}.")

        # Сбор твитов
        tweets = collect_tweets(keyword, date)
        if not tweets:
            await message.answer("Не удалось собрать твиты. Попробуйте позже.")
            await state.clear()
            return

        # Анализ твитов
        sentiment_map = {
            "positive": 0,
            "negative": 1,
            "raid": 2,
            "indirect_mention": 3,
            "mention": 3  # Обработка "mention" как "indirect_mention"
        }

        results = []
        positive, negative, raid, indirect_mention = 0, 0, 0, 0

        for tweet in tweets:
            sentiment = predict_sentiment(tweet["tweet"], "./bert_sentiment_model")
            if sentiment in sentiment_map:
                sentiment_label = sentiment
                results.append({"tweet": tweet["tweet"], "sentiment": sentiment_label})

                if sentiment_label == "positive":
                    positive += 1
                elif sentiment_label == "negative":
                    negative += 1
                elif sentiment_label == "raid":
                    raid += 1
                elif sentiment_label in ["indirect_mention", "mention"]:
                    indirect_mention += 1
            else:
                logging.error(f"Некорректное значение sentiment: {sentiment}")

        # Подсчет общей статистики
        total_tweets = len(tweets)
        interest_index = round((positive * 0.6 + raid * 0.3 + indirect_mention * 0.1) / total_tweets, 2) if total_tweets else 0

        # Сохранение результатов в историю
        history_data = {
            "keyword": keyword,
            "date": date,
            "total_tweets": total_tweets,
            "positive": positive,
            "negative": negative,
            "raid": raid,
            "indirect_mention": indirect_mention,
            "interest_index": interest_index
        }
        history_df = pd.DataFrame([history_data])
        if not pd.io.common.file_exists("history.csv"):
            history_df.to_csv("history.csv", index=False)
        else:
            existing_df = pd.read_csv("history.csv")
            combined_df = pd.concat([existing_df, history_df], ignore_index=True)
            combined_df.to_csv("history.csv", index=False)

        # Отправка результатов пользователю
        await message.answer(
            f"📊 Результаты анализа:\n\n"
            f"📋 Всего твитов: {total_tweets}\n"
            f"➕ Позитивные: {positive} ({(positive / total_tweets * 100):.2f}%)\n"
            f"➖ Негативные: {negative} ({(negative / total_tweets * 100):.2f}%)\n"
            f"🎯 Рейдовые упоминания: {raid} ({(raid / total_tweets * 100):.2f}%)\n"
            f"📢 Косвенные упоминания: {indirect_mention} ({(indirect_mention / total_tweets * 100):.2f}%)\n\n"
            f"📈 Индекс заинтересованности: {interest_index}"
        )

        await state.clear()

    except ValueError as e:
        await message.answer(f"Ошибка: {str(e)}. Попробуйте снова.")


@dp.message(lambda message: message.text == "📊 Посмотреть результаты")
async def show_results(message: Message):
    try:
        df = pd.read_csv("history.csv")
        if df.empty:
            await message.answer("История запросов пуста.")
            return

        history = df.tail(5).to_dict(orient="records")
        response = "📋 Последние запросы:\n\n"
        for entry in history:
            response += (
                f"📊 Результаты анализа:\n\n"
                f"📋 Всего твитов: {entry['total_tweets']}\n"
                f"➕ Позитивные: {entry['positive']} ({(entry['positive'] / entry['total_tweets'] * 100):.2f}%)\n"
                f"➖ Негативные: {entry['negative']} ({(entry['negative'] / entry['total_tweets'] * 100):.2f}%)\n"
                f"🎯 Рейдовые упоминания: {entry['raid']} ({(entry['raid'] / entry['total_tweets'] * 100):.2f}%)\n"
                f"📢 Косвенные упоминания: {entry['indirect_mention']} ({(entry['indirect_mention'] / entry['total_tweets'] * 100):.2f}%)\n\n"
                f"📈 Индекс заинтересованности: {entry['interest_index']}\n\n"
            )

        await message.answer(response)
    except Exception as e:
        logging.error(f"Ошибка при чтении истории: {e}")
        await message.answer("Не удалось загрузить историю запросов.")


# Запуск бота
async def main():
    logging.info("Запуск бота...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
