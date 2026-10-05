from .ml_engine import predict_text, predict_url

def calculate_risk(text: str, urls: list, se_signals: dict, struct_scores: dict) -> dict:
    """
    Hybrid risk engine combining ML prediction with existing structural signals.
    """
    # 1. Get ML probabilities
    text_res = predict_text(text)
    text_prob = text_res["probability"]
    
    url_probs = [predict_url(u)["probability"] for u in urls]
    url_prob = max(url_probs) if url_probs else 0.0
    
    # Base risk starts from ML prediction (weighted heavily)
    # If it's very likely phishing/malicious, base risk is high.
    ml_base_risk = max(text_prob, url_prob) * 100
    
    # 2. Add structural / SE signal risk
    se_score = 0
    se_weights = {
        "urgency": 8, "fear_threat": 10, "authority": 8, "reward": 8,
        "financial_pressure": 12, "credential_request": 15,
        "curiosity": 5, "emotional": 5
    }
    
    for k, w in se_weights.items():
        if se_signals.get(k, {}).get("present"):
            se_score += w
            
    # URL structural score
    url_struct_score = sum([u_score.get("added_risk", 0) for u_score in struct_scores.get("url_results", [])])
    
    # 3. Combine scores
    # ML probability is the anchor (max 60% contribution to final score if highly certain).
    # Remaining 40% comes from deterministic signals.
    combined_score = (ml_base_risk * 0.6) + min(se_score + url_struct_score, 40)
    
    if combined_score < 5 and not text.strip() and not urls:
        combined_score = 5
        
    final_score = int(max(0, min(100, round(combined_score))))
    
    # Risk Level
    if final_score >= 75:
        level = "Critical"
    elif final_score >= 55:
        level = "High"
    elif final_score >= 30:
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
