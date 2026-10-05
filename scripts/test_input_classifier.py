import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.input_detection.input_classifier import detect_input_type

def run_tests():
    print("Running Input Detection Tests...\n")
    
    # TEST 1
    res1 = detect_input_type("https://example.com")
    print("TEST 1 (URL):", res1["primary_type"], "->", res1["routing"])
    assert res1["primary_type"] == "URL"
    
    # TEST 2
    res2 = detect_input_type("Congratulations! You have won a prize. Click here...")
    print("TEST 2 (Text):", res2["primary_type"], "->", res2["routing"])
    assert res2["primary_type"] == "Text / Message"
    
    # TEST 3
    res3 = detect_input_type("Verify your account at https://example.com/login")
    print("TEST 3 (Text + URL):", res3["primary_type"], "->", res3["routing"])
    assert res3["primary_type"] == "Text + URL"
    
    # TEST 7
    res7 = detect_input_type("")
    print("TEST 7 (Empty):", res7["primary_type"], "->", res7["routing"])
    assert res7["primary_type"] == "Unknown"
    
    # TEST 8
    res8 = detect_input_type("http://[malformed-url]")
    print("TEST 8 (Malformed URL):", res8["primary_type"], "->", res8["routing"])
    
    print("\nAll text tests passed. (Image tests skipped in unit test script due to missing mocks).")

if __name__ == "__main__":
    run_tests()
