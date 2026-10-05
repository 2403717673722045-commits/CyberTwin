import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.models.model_loader import get_text_model, get_url_model

def test_loading():
    print("Testing text model loading...")
    text_model = get_text_model()
    if text_model:
        print("Text model loaded successfully.")
    else:
        print("Failed to load text model.")
        exit(1)
        
    print("Testing URL model loading...")
    url_model = get_url_model()
    if url_model:
        print("URL model loaded successfully.")
    else:
        print("Failed to load URL model.")
        exit(1)
        
if __name__ == "__main__":
    test_loading()
