# CyberTwin ML Integration

This directory contains the ML infrastructure that powers CyberTwin's threat detection.

## Setup & Reproducibility

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Download datasets:**
   ```bash
   python src/data/download_data.py
   ```
3. **Train Models:**
   - Text classification model:
     ```bash
     python src/models/train_text_model.py
     ```
   - URL classification model:
     ```bash
     python src/models/train_url_model.py
     ```
4. **Run Application:**
   ```bash
   streamlit run app.py
   ```

## Model Pipeline

- **Text Model:** 
  - *Data*: UCI SMS Spam Collection
  - *Preprocessing*: Text normalization, TF-IDF + N-Grams, Structural features extraction (regex).
  - *Dimensionality Reduction*: TruncatedSVD for sparse TF-IDF matrices.
  - *Classifier*: Logistic Regression.
- **URL Model:**
  - *Data*: Phishing Websites dataset.
  - *Preprocessing*: Extraction of length, count of special characters, protocol, hostname properties.
  - *Classifier*: Random Forest.

## Risk Engine
Inference results from both the Text and URL models are passed into `src/models/risk_engine.py`, which forms a hybrid threat score combining the ML probability outputs with heuristic social-engineering structural flags.
