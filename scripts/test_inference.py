import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.models.ml_engine import predict_text, predict_url
from src.models.risk_engine import calculate_risk

def test_inference():
    print("Testing Text Inference...")
    res = predict_text("Your account will be blocked. Verify now at http://example.com/login with OTP.")
    print("Result:", res)
    
    print("\nTesting URL Inference...")
    res_url = predict_url("http://example.com/login")
    print("Result:", res_url)
    
    print("\nTesting Risk Engine...")
    risk_res = calculate_risk(
        "Your account will be blocked. Verify now at http://example.com/login with OTP.", 
        ["http://example.com/login"], 
        {"credential_request": {"present": True}, "urgency": {"present": True}}, 
        {"url_results": []}
    )
    print("Result:", risk_res)

if __name__ == "__main__":
    test_inference()
