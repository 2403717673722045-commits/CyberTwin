import os
import joblib
import json

def _load_model(model_path):
    if not os.path.exists(model_path):
        return None
    try:
        return joblib.load(model_path)
    except Exception as e:
        print(f"Error loading model {model_path}: {e}")
        return None

def get_text_model():
    path = os.path.join(os.path.dirname(__file__), "..", "..", "models", "text", "final_text_model.joblib")
    return _load_model(path)

def get_url_model():
    path = os.path.join(os.path.dirname(__file__), "..", "..", "models", "url", "final_url_model.joblib")
    return _load_model(path)
