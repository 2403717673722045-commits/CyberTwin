import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.models.model_loader import get_url_model
from src.features.url_features import extract_url_features
from src.models.risk_engine import calculate_risk
from src.models.ml_engine import predict_url

def test_diagnostics():
    print("====================================")
    print("CYBERTWIN URL MODEL DIAGNOSTICS")
    print("====================================")
    
    test_urls = [
        "https://www.google.com",
        "https://www.microsoft.com",
        "https://www.apple.com",
        "https://www.wikipedia.org",
        "http://hdfc-secure-verify.tk/login"
    ]
    
    for u in test_urls:
        print(f"\nURL: {u}")
        print("Features:", extract_url_features([u])[0])
        res = predict_url(u)
        print(f"ML probability: {res['probability']:.4f}")
        print(f"Predicted: {res['prediction']}")
        
        risk_res = calculate_risk("", [u], {}, {"url_results": []})
        print(f"Final risk: {risk_res['risk_score']} ({risk_res['risk_level']})")

if __name__ == "__main__":
    test_diagnostics()
