import torch  
import pandas as pd
from sklearn.model_selection import train_test_split
from torch.utils.data import Dataset
from transformers import BertTokenizer


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
    data = pd.read_csv(file_path)
    data["sentiment"] = data["sentiment"].map({"positive": 1, "negative": 0})

    train_texts, val_texts, train_labels, val_labels = train_test_split(
        data["tweet"], data["sentiment"], test_size=0.2, random_state=42
    )

    tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")

    train_dataset = SentimentDataset(train_texts.tolist(), train_labels.tolist(), tokenizer, max_len)
    val_dataset = SentimentDataset(val_texts.tolist(), val_labels.tolist(), tokenizer, max_len)

    return train_dataset, val_dataset, tokenizer
