from .ml_engine import predict_text, predict_url

def calculate_risk(text: str, urls: list, se_signals: dict, struct_scores: dict) -> dict:
    """
    Multimodal Risk Engine: Fusion of ML predictions and structured social-engineering/URL signals.
    """
    # 1. Get ML probabilities
    text_res = predict_text(text)
    text_prob = text_res["probability"]
    
    url_probs = [predict_url(u)["probability"] for u in urls]
    url_prob = max(url_probs) if url_probs else 0.0
    
    # 2. Add structural / SE signal risk
    se_score = 0
    se_weights = {
        "urgency": 10, "fear_threat": 12, "authority": 10, "reward": 8,
        "financial_pressure": 15, "credential_request": 20,
        "curiosity": 5, "emotional": 5
    }
    
    active_se_signals = []
    for k, w in se_weights.items():
        if se_signals.get(k, {}).get("present"):
            se_score += w
            active_se_signals.append(k)
            
    # URL structural score
    url_struct_score = sum([u_score.get("added_risk", 0) for u_score in struct_scores.get("url_results", [])])
    
    # 3. Multi-Signal Fusion Logic
    # CyberTwin combines signals dynamically.
    base_ml_risk = max(text_prob, url_prob) * 100
    
    # Synergistic risk multiplier: If ML predicts a threat AND there are strong SE signals (e.g. credential theft)
    multiplier = 1.0
    if base_ml_risk > 40 and ("credential_request" in active_se_signals or "financial_pressure" in active_se_signals):
        multiplier = 1.25 # Contextual relationship amplifying risk
        
    # Total score combines weighted ML output with deterministic flags
    combined_score = (base_ml_risk * 0.5) * multiplier + (se_score * 1.5) + url_struct_score
    
    # Additional penalty if both Text ML and URL ML independently flag it as high risk (multimodal confirmation)
    if text_prob > 0.6 and url_prob > 0.6:
        combined_score += 15
        
    if combined_score < 5 and not text.strip() and not urls:
        combined_score = 5
        
    final_score = int(max(0, min(100, round(combined_score))))
    
    # Risk Level
    if final_score >= 80:
        level = "Critical"
    elif final_score >= 60:
        level = "High"
    elif final_score >= 35:
        level = "Medium"
    else:
        level = "Low"
        
    return {
        "risk_score": final_score,
        "risk_level": level,
        "ml_probability": round(max(text_prob, url_prob) * 100, 1),
        "security_signal_score": se_score,
        "url_score": url_struct_score
    }
