import pandas as pd

def normalize_dataset(file_path, output_path):
    data = pd.read_csv(file_path)

    mapping = {
        "positive": "positive",
        "negative": "negative",
        "raid": "raid",
        "indirect_mention": "mention"  
    }

    data["sentiment"] = data["sentiment"].map(mapping)

    data = data.dropna(subset=["sentiment"])

    data = data.drop_duplicates(subset=["tweet", "user", "date"])

    data.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"Нормализованный файл сохранён как: {output_path}")

normalize_dataset("collected_tweets.csv", "normalized_tweets.csv")
