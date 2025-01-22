from twitter_auth import twitter_login
from twitter_parser import collect_tweets
from sentiment_model import train_model, predict_sentiment
from data import prepare_data

DATA_PATH = "tweets_data.csv"
MODEL_PATH = "./bert_sentiment_model"

def main():
    print("Авторизация в Twitter...")
    twitter_login()

    print("Сбор твитов...")
    query = "$coby"
    target_date = "2025-01-20"
    collect_tweets(query, target_date)

    print("Подготовка данных...")
    train_dataset, val_dataset, tokenizer = prepare_data(DATA_PATH)

    print("Обучение модели...")
    train_model(train_dataset, val_dataset, tokenizer, MODEL_PATH)

    test_tweet = "I think $COBY is a total scam and waste of money."
    sentiment = predict_sentiment(test_tweet, MODEL_PATH)
    print(f"Tweet: {test_tweet}")
    print(f"Sentiment: {'positive' if sentiment == 1 else 'negative'}")


if __name__ == "__main__":
    main()
