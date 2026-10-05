from src.models.model_loader import get_text_model, get_url_model

def predict_text(text: str) -> dict:
    """Predict text threat. Returns probability of Phishing/Scam (1)."""
    model = get_text_model()
    if model is None or not text.strip():
        return {"probability": 0.0, "prediction": "Benign"}
        
    prob = model.predict_proba([text])[0][1]
    pred = "Phishing/Scam" if prob > 0.5 else "Benign"
    return {"probability": float(prob), "prediction": pred}

def predict_url(url: str) -> dict:
    """Predict URL threat. Returns probability of Phishing/Malicious (1)."""
    model = get_url_model()
    if model is None or not url.strip():
        return {"probability": 0.0, "prediction": "Benign"}
        
    prob = model.predict_proba([url])[0][1]
    pred = "Phishing/Malicious" if prob > 0.5 else "Benign"
    return {"probability": float(prob), "prediction": pred}
