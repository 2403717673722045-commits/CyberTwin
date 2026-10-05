import re
import numpy as np

def extract_text_features(texts):
    features = []
    for text in texts:
        text = str(text)
        features.append([
            len(text),
            len(text.split()),
            len(re.findall(r'\d', text)),
            sum(1 for c in text if c.isupper()),
            len(re.findall(r'[!@#$%^&*(),.?":{}|<>]', text)),
            len(re.findall(r'(https?://[^\s]+|www\.[^\s]+)', text)),
            len(re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)),
            len(re.findall(r'(?:\+?91[\s-]?)?[6-9]\d{9}|\+\d[\d\s-]{7,}\d', text)),
            len(re.findall(r'(?:₹|Rs\.?|\$|£|€)', text)),
            len(re.findall(r'\b(urgent|immediately|right now|last chance)\b', text.lower())),
            len(re.findall(r'\b(otp|password|pin|cvv|account|verify)\b', text.lower())),
            len(re.findall(r'\b(won|winner|lottery|prize|free)\b', text.lower()))
        ])
    return np.array(features)
