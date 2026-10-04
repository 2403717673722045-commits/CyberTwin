# CyberTwin — AI-Powered Counterfactual Cyber-Risk Simulator

Detect → Explain → Simulate → Protect → Report → Track → Learn

## Folder structure
```
CyberTwin/
├── app.py                 # main integrated Streamlit app (all modules)
├── threat_engine.py       # normalization + TF-IDF prototype semantics + URL/SE signals + risk score
├── simulation_engine.py   # Proceed / Ignore / Verify / Report counterfactual paths
├── incident_engine.py     # protection & recovery plans per incident stage
├── report_generator.py    # editable complaint draft (never fabricates official numbers)
├── copilot.py             # contextual rule-based copilot (LLM upgrade point)
├── requirements.txt
├── data/                  # optional datasets (empty for MVP)
└── reports/               # downloaded complaints land here if you save them
```

## Install & run (Windows)
```powershell
cd "E:\MSC - 3rd yr\CyberTwin"
pip install -r requirements.txt
streamlit run app.py
```
Then open the URL shown (usually http://localhost:8501).

## Demo flow for judges (2 min)
1. **Dashboard** → Load demo case → goes to Threat Analysis.
2. **Threat Analysis** → Analyse → see risk score, threat type, indicators, URLs, signals.
3. **What-If Simulator** → pick Proceed vs Verify → show attack chain + risk comparison.
4. **Protection** → pick "Entered credentials" → checklist.
5. **Evidence** → Save → **Complaint Generator** → Generate → Download .txt.
6. **AI Copilot** → ask "Why is this risky?"
7. **Awareness Training** → answer quiz.

## Upgrade points (for team of 4)
- `threat_engine.semantic_scores()` → replace TF-IDF with sentence embeddings + LogisticRegression/XGBoost trained on labelled scam dataset.
- `threat_engine.classify_threat()` → plug trained classifier; keep same return contract.
- `copilot.answer_question()` → plug LLM with `analysis` dict as context.
- Add QR decode (`pyzbar`) + screenshot OCR (`pytesseract`) as new inputs feeding `analyze_threat()`.

## Responsible design
- No fake accuracy, no fake complaint numbers/status, no threat-intel claims.
- Simulations labelled plausible, not certain. Tracking labelled internal/user-entered.
- Never asks for real passwords/OTPs; UPI/transaction values masked.
