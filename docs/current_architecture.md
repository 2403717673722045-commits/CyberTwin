# CyberTwin - Current Architecture & ML Migration Plan

## 1. Existing Modules & Functionality
CyberTwin is currently structured as a monolithic Streamlit application with several backend modules that process input data deterministically:
- **`app.py`**: The Streamlit frontend. It manages the UI across 11 pages (Dashboard, Threat Analysis, URL Analysis, Simulator, etc.) and uses `st.session_state` to share analysis results (like `analysis`, `evidence`, `history`).
- **`threat_engine.py`**: The core detection layer. It contains text normalization, URL extraction, social engineering pattern matching (via regex), and heuristic risk scoring.
- **`simulation_engine.py`**: A counterfactual simulator that provides static, rule-based consequence chains based on the threat type and risk score.
- **`incident_engine.py`**: Provides protection and recovery guidance based on the incident stage.
- **`report_generator.py`**: Formats evidence and threat analysis into textual complaint drafts.
- **`copilot.py`**: A contextual rule-based conversational assistant using regex.
- **`media_utils.py`**: Helpers for OCR and QR decoding.

## 2. Current ML & Rule-Based Components
- **Rule-Based Components**:
  - Social engineering detection uses predefined regex patterns (e.g., `SE_PATTERNS`).
  - URL analysis looks for predefined suspicious characteristics (e.g., length, punycode, specific TLDs).
  - Risk score is a manually tuned weighted sum of these heuristic flags.
- **Current ML Components**:
  - The closest thing to ML is `semantic_scores()` in `threat_engine.py`. It uses a `TfidfVectorizer` and `cosine_similarity` to compare user input to a small, hardcoded list of threat prototypes. This is NOT a predictive ML model; it is simply prototype matching.

## 3. Problems with Current Architecture
- **No Learned Patterns**: The system relies entirely on predefined rules and cannot adapt to novel phrasing or new threats without manual regex updates.
- **Manual Weighting**: The risk score is composed of arbitrary weights that haven't been calibrated against real-world distributions.
- **Rigid Semantic Matching**: Prototype-based cosine similarity scales poorly and suffers from high false-positive rates when benign text shares keywords with threats.
- **Lack of Confidence Calibration**: Confidence scores are heuristic ("High" if score >= 60) rather than probability-based.

## 4. Proposed ML Architecture
We will introduce a dedicated ML inference layer while retaining the existing application flow.
- **New Data Pipeline**: Proper separation of raw, processed, and external datasets.
- **New ML Layer (`src/models/`, `models/`)**: Two separate classification models will be built:
  - **Text Model**: Classifies message text (Benign vs. Phishing/Spam) using TF-IDF and NLP features.
  - **URL Model**: Classifies URLs (Benign vs. Malicious) using structural and lexical features.
- **Risk Engine Revision (`src/models/risk_engine.py`)**: A hybrid risk engine that combines the calibrated probabilities from the ML models with the existing structural/SE signals from `threat_engine.py` to produce a transparent risk score.
- **Streamlit Integration**: `app.py` will load pre-trained `.joblib` models and use them during the "Analyze Threat" workflow, passing ML probabilities into the Personal Cyber Twin and Attacker's Perspective modules.
- **ML Model Lab Page**: A new Streamlit page displaying evaluation metrics, confusion matrices, and feature importance to provide transparency into model performance.

## 5. Files to be Added
- `docs/current_architecture.md`
- `data/DATASET_INFO.md`
- `src/data/download_data.py`, `src/data/make_dataset.py`
- `src/features/build_features.py`
- `src/models/train_text_model.py`, `src/models/train_url_model.py`
- `src/models/risk_engine.py`, `src/models/ml_engine.py`
- `models/text/...`, `models/url/...`, `models/metadata/...`
- `notebooks/01_data_exploration.ipynb` to `05_model_evaluation.ipynb`
- `tests/test_ml.py`
- `README_ML.md`
- `requirements.txt` (updated)

## 6. Files to be Modified
- **`app.py`**: Add ML Model Lab page, load ML models, update Threat Analysis page to show ML output.
- **`threat_engine.py`**: Refactor to call `ml_engine.py` and `risk_engine.py`.
- **`simulation_engine.py` / `incident_engine.py`**: Update slightly if new ML threat types emerge.
- **`copilot.py`**: Incorporate ML probability and explanations into responses.
- **`requirements.txt`**: Add `scikit-learn`, `pandas`, `pytest`, `matplotlib`, `seaborn` etc.
