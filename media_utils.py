"""
CyberTwin - media_utils.py (NEW, additive)
Screenshot OCR + QR decoding helpers feeding the existing threat workflow.

Screenshot: Upload image -> OCR (pytesseract if available) -> text -> analyze_threat()
QR: Upload QR image -> decode (OpenCV QRCodeDetector) -> URL/payment text -> analyze_threat()

Both degrade gracefully if optional deps / binaries are missing.
"""
from __future__ import annotations

def ocr_image(pil_image) -> dict:
    """Return {text, urls_hint, available, message}."""
    try:
        import pytesseract
        text = pytesseract.image_to_string(pil_image) or ""
        text = text.strip()
        if not text:
            return {"text": "", "available": True,
                    "message": "OCR ran but found no readable text. Try a clearer screenshot or paste the text manually."}
        return {"text": text, "available": True, "message": "OCR extracted text successfully."}
    except ImportError:
        return {"text": "", "available": False,
                "message": "pytesseract not installed. Run: pip install pytesseract Pillow, plus install Tesseract-OCR binary (Windows: https://github.com/UB-Mannheim/tesseract/wiki). You can still paste the text manually."}
    except Exception as e:
        # usually TesseractNotFoundError when binary missing
        return {"text": "", "available": False,
                "message": f"OCR unavailable ({e}). Install Tesseract binary (Windows: https://github.com/UB-Mannheim/tesseract/wiki) or paste text manually."}


def decode_qr(pil_image) -> dict:
    """Return {data, kind, available, message}. kind in url/payment/text/none."""
    try:
        import cv2
        import numpy as np
    except ImportError:
        return {"data": "", "kind": "none", "available": False,
                "message": "opencv-python not installed. Run: pip install opencv-python. You can still type the QR content manually."}
    try:
        import numpy as np
        img = pil_image.convert("RGB")
        arr = np.array(img)
        arr_bgr = arr[:, :, ::-1]  # RGB -> BGR for OpenCV
        det = cv2.QRCodeDetector()
        data, points, _ = det.detectAndDecode(arr_bgr)
        data = (data or "").strip()
        if not data:
            # try multi
            try:
                ok, decoded, pts, _ = det.detectAndDecodeMulti(arr_bgr)
                if ok and decoded:
                    data = "; ".join(d for d in decoded if d).strip()
            except Exception:
                pass
        if not data:
            return {"data": "", "kind": "none", "available": True,
                    "message": "No QR code detected. Try a clearer, uncropped QR image."}
        low = data.lower()
        if low.startswith(("http://", "https://", "www.")) or "upi://" in low or "upi.pay" in low:
            kind = "url" if low.startswith(("http", "www.")) else "payment"
            if "upi" in low or low.startswith("upi://"):
                kind = "payment"
        elif "@" in data and (low.endswith(("upi", "ybl", "okhdfc", "paytm")) or "/pay" in low or "pa=" in low or "pn=" in low):
            kind = "payment"
        else:
            kind = "text"
        return {"data": data, "kind": kind, "available": True, "message": f"QR decoded ({kind}). Sent to threat analysis."}
    except Exception as e:
        return {"data": "", "kind": "none", "available": True, "message": f"QR decode failed: {e}"}
