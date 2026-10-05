import os
import numpy as np

try:
    import tensorflow as tf
    from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input, decode_predictions
    from tensorflow.keras.preprocessing.image import img_to_array
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

# Load MobileNetV2 globally if TF is available
_cnn_model = None

def get_cnn_model():
    global _cnn_model
    if TF_AVAILABLE and _cnn_model is None:
        try:
            # Load MobileNetV2 pre-trained on ImageNet
            _cnn_model = MobileNetV2(weights='imagenet')
        except Exception:
            _cnn_model = None
    return _cnn_model

def classify_image_cnn(pil_img) -> dict:
    """
    Uses a CNN (MobileNetV2) to extract visual features and classify the image.
    This helps in identifying generic objects or UI elements if trained further.
    """
    res = {
        "cnn_available": False,
        "predictions": [],
        "image_type": "Unknown",
        "suspicious_visuals": False
    }
    
    model = get_cnn_model()
    if model is None or pil_img is None:
        return res
        
    res["cnn_available"] = True
    
    try:
        # Preprocess for MobileNetV2
        img = pil_img.resize((224, 224))
        x = img_to_array(img)
        x = np.expand_dims(x, axis=0)
        x = preprocess_input(x)
        
        # Predict
        preds = model.predict(x, verbose=0)
        decoded = decode_predictions(preds, top=3)[0]
        
        # Format predictions
        pred_labels = []
        for _, label, prob in decoded:
            pred_labels.append(f"{label} ({prob*100:.1f}%)")
            
        res["predictions"] = pred_labels
        
        # Heuristics for cybersecurity UI detection (Mocking deeper fine-tuning)
        # In a fully deployed system, this would be a fine-tuned CNN for "login screens"
        labels_str = " ".join([l for _, l, _ in decoded]).lower()
        if any(w in labels_str for w in ["web_site", "monitor", "screen", "cellular_telephone", "envelope"]):
            res["image_type"] = "Digital Screen / Interface"
        else:
            res["image_type"] = "Photograph / Object"
            
    except Exception as e:
        res["error"] = str(e)
        
    return res
