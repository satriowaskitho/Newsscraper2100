from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F

# Load model dan tokenizer IndoBERT yang sudah dilatih untuk sentimen analisis
MODEL_NAME = "w11wo/indonesian-roberta-base-sentiment-classifier"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

# Label sesuai urutan output model (lihat dari deskripsi model)
ID2LABEL = {
    0: "negatif",
    1: "netral",
    2: "positif"
}

def classify_sentiment_id_bert(text_id: str) -> str:
    """
    Klasifikasi sentimen teks Bahasa Indonesia menggunakan IndoBERT.
    Output: 'positif', 'negatif', atau 'netral'.
    """
    try:
        inputs = tokenizer(text_id, return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            probs = F.softmax(logits, dim=-1)
            pred_class = torch.argmax(probs, dim=1).item()
            return ID2LABEL[pred_class]
    except Exception as e:
        return f"error: {e}"
