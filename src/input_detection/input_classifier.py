import re
from typing import Dict, Any, Tuple

def extract_urls(text: str) -> list:
    if not text:
        return []
    # simple URL regex
    url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
    urls = re.findall(url_pattern, text)
    return urls

def detect_input_type(text_input: str = "", image_pil=None) -> Dict[str, Any]:
    text_input = text_input.strip() if text_input else ""
    
    res = {
        "primary_type": "Unknown",
        "detection_method": "Deterministic Rules",
        "components": [],
        "routing": [],
        "extracted_text": "",
        "extracted_urls": []
    }
    
    if image_pil:
        # process image
        from media_utils import ocr_image, decode_qr
        from src.models.image_engine import classify_image_cnn
        
        qr_data = ""
        ocr_text = ""
        
        # 1. Run CNN Classification
        cnn_res = classify_image_cnn(image_pil)
        if cnn_res.get("cnn_available"):
            res["components"].append("CNN Image Classifier")
            res["detection_method"] = f"CNN ({cnn_res['image_type']})"
        
        # 2. Run QR Decoder
        qr_res = decode_qr(image_pil)
        if qr_res["data"]:
            qr_data = qr_res["data"]
            res["components"].append("QR Decoder")
            
        ocr_res = ocr_image(image_pil)
        if ocr_res["text"]:
            ocr_text = ocr_res["text"]
            res["components"].append("OCR")
            
        if qr_data and ocr_text:
            res["primary_type"] = "Image containing QR + text"
            res["detection_method"] = "Image analysis (QR + OCR)"
            res["extracted_text"] = ocr_text
            res["extracted_urls"] = [qr_data] if qr_data.startswith(("http", "www")) else []
            if not res["extracted_urls"] and qr_data:
                res["extracted_text"] += "\n[QR Data]: " + qr_data
        elif qr_data:
            res["primary_type"] = "QR Code"
            res["detection_method"] = "QR decoder"
            res["extracted_urls"] = [qr_data] if qr_data.startswith(("http", "www")) else []
            if not res["extracted_urls"]:
                res["extracted_text"] = qr_data
        elif ocr_text:
            res["primary_type"] = "Screenshot with text"
            res["detection_method"] = "Image analysis + OCR"
            res["extracted_text"] = ocr_text
            urls_in_ocr = extract_urls(ocr_text)
            res["extracted_urls"] = urls_in_ocr
        else:
            res["primary_type"] = "Image (No readable text/QR)"
            if "CNN" not in res["detection_method"]:
                res["detection_method"] = "Image analysis (Failed to find content)"
                
        if cnn_res.get("cnn_available"):
            res["cnn_predictions"] = cnn_res["predictions"]
            res["image_type"] = cnn_res["image_type"]
            
    elif text_input:
        urls = extract_urls(text_input)
        if not urls:
            res["primary_type"] = "Text / Message"
            res["detection_method"] = "Text analysis (No URLs)"
            res["extracted_text"] = text_input
            res["components"].append("Text")
        else:
            res["extracted_urls"] = urls
            res["components"].append("URL")
            
            # Check if it's purely a URL
            if len(urls) == 1 and urls[0].strip() == text_input.strip():
                res["primary_type"] = "URL"
                res["detection_method"] = "URL parser"
            else:
                res["primary_type"] = "Text + URL"
                res["detection_method"] = "Text + URL parser"
                res["extracted_text"] = text_input
                res["components"].insert(0, "Text")
                
    # Build routing based on extracted content
    if res["extracted_urls"]:
        res["routing"].append("URL ML Model")
    if res["extracted_text"] and len(res["extracted_text"].strip()) > 5:
        # Ignore extremely short strings for Text ML to avoid noisy routing
        res["routing"].append("Text ML Model")
        
    return res
