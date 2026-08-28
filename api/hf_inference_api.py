Huffingface inference_mode FastAPI

from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

app = FastAPI(title="HuggingFace Inference API")

# Load FinBERT
tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")

class InferenceRequest(BaseModel):
    symbol: str
    text: str

class InferenceResponse(BaseModel):
    hf_sentiment: float
    positive: float
    negative: float
    neutral: float

@app.post("/hf/sentiment", response_model=InferenceResponse)
async def hf_sentiment(req: InferenceRequest):
    inputs = tokenizer(req.text, return_tensors="pt", truncation=True)
    outputs = model(**inputs)
    scores = torch.softmax(outputs.logits, dim=1).tolist()[0]

    return InferenceResponse(
        hf_sentiment=scores[2] - scores[0],
        positive=scores[2],
        negative=scores[0],
        neutral=scores[1],
    )
