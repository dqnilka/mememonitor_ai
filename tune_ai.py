from transformers import BertForSequenceClassification, BertTokenizer, Trainer, TrainingArguments, DataCollatorWithPadding
import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from torch.utils.data import Dataset
import os
import logging

logging.basicConfig(level=logging.INFO)

class SentimentDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_len):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, index):
        text = self.texts[index]
        label = self.labels[index]

        encoding = self.tokenizer(
            text,
            max_length=self.max_len,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )

        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "labels": torch.tensor(label, dtype=torch.long),
        }


def prepare_data(file_path, max_len=128):
    logging.info("Чтение данных из файла: %s", file_path)
    data = pd.read_csv(file_path)
    data["sentiment"] = data["sentiment"].map({
        "positive": 0,
        "negative": 1,
        "raid": 2,
        "mention": 3
    })

    train_texts, val_texts, train_labels, val_labels = train_test_split(
        data["tweet"], data["sentiment"], test_size=0.2, random_state=42
    )

    logging.info("Инициализация токенизатора...")
    tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")

    train_dataset = SentimentDataset(train_texts.tolist(), train_labels.tolist(), tokenizer, max_len)
    val_dataset = SentimentDataset(val_texts.tolist(), val_labels.tolist(), tokenizer, max_len)

    logging.info("Данные подготовлены.")
    return train_dataset, val_dataset, tokenizer


def train_model(train_dataset, val_dataset, tokenizer, model_path):
    logging.info("Инициализация модели...")
    model = BertForSequenceClassification.from_pretrained("bert-base-uncased", num_labels=4)

    log_dir = "./logs"
    if os.path.exists(log_dir):
        if not os.path.isdir(log_dir):
            os.remove(log_dir)  
            os.makedirs(log_dir)  
    else:
        os.makedirs(log_dir)
    logging.info("Директория %s уже существует.", log_dir)

    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    training_args = TrainingArguments(
        output_dir="./results",
        eval_strategy="steps", 
        save_strategy="steps",
        save_steps=500,
        eval_steps=500,
        load_best_model_at_end=True,
        per_device_train_batch_size=8,  
        per_device_eval_batch_size=8,
        num_train_epochs=3,
        logging_dir=log_dir,
        logging_steps=100,
        save_total_limit=1,
        report_to="none",  
    )

    logging.info("Инициализация Trainer...")
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=data_collator,
    )

    logging.info("Начало обучения модели...")
    trainer.train()
    model.save_pretrained(model_path)
    tokenizer.save_pretrained(model_path)
    logging.info("Модель успешно обучена и сохранена в %s", model_path)


if __name__ == "__main__":
    DATA_PATH = "normalized_tweets.csv"  
    MODEL_PATH = "./bert_sentiment_model"

    logging.info("Подготовка данных...")
    train_dataset, val_dataset, tokenizer = prepare_data(DATA_PATH)

    logging.info("Обучение модели...")
    train_model(train_dataset, val_dataset, tokenizer, MODEL_PATH)
