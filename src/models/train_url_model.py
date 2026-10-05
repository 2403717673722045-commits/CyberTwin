import pandas as pd
import numpy as np
import os
import joblib
import json
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, FunctionTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                             roc_auc_score, confusion_matrix)
import matplotlib
matplotlib.use("Agg")  # headless-safe figure generation
import matplotlib.pyplot as plt
import seaborn as sns
import re
from urllib.parse import urlparse
from src.features.url_features import extract_url_features

FIG_DIR = os.path.join("reports", "figures")
URL_MODEL_DIR = os.path.join("models", "url")
META_DIR = os.path.join("models", "metadata")

def train_url_model():
    print("Loading URL dataset...")
    os.makedirs(FIG_DIR, exist_ok=True)
    os.makedirs(URL_MODEL_DIR, exist_ok=True)
    os.makedirs(META_DIR, exist_ok=True)
    data_path = os.path.join("data", "raw", "urldata.csv")
    
    # Read the dataset. Since the URL dataset might have different columns, let's assume it has 'domain' and 'label'
    try:
        df = pd.read_csv(data_path)
    except FileNotFoundError:
        print("URL dataset not found.")
        return
        
    # The shreyagopal dataset has 'Domain' and 'Label' or similar
    if 'url' in df.columns.str.lower():
        url_col = df.columns[df.columns.str.lower() == 'url'][0]
    elif 'domain' in df.columns.str.lower():
        url_col = df.columns[df.columns.str.lower() == 'domain'][0]
    else:
        url_col = df.columns[0]
        
    if 'label' in df.columns.str.lower():
        label_col = df.columns[df.columns.str.lower() == 'label'][0]
    else:
        label_col = df.columns[-1]

    # Map labels: 0 -> Benign, 1 -> Phishing
    # Some datasets use 0 and 1, others use 'good' and 'bad'
    if df[label_col].dtype == object:
        df['target'] = df[label_col].apply(lambda x: 1 if str(x).lower() in ['bad', 'phishing', '1'] else 0)
    else:
        df['target'] = df[label_col]
    assert set(df['target'].dropna().unique()) <= {0, 1}, \
        f"unexpected URL label values: {df['target'].unique()}"
        
    print(f"Original shape: {df.shape}")
    df = df.drop_duplicates().reset_index(drop=True)
    
    # Subsample if too large for quick processing
    if len(df) > 50000:
        df = df.sample(50000, random_state=42).reset_index(drop=True)
        
    print(f"Shape after duplicate removal and subsampling: {df.shape}")
    print(f"Class distribution:\n{df['target'].value_counts(normalize=True)}")
    
    X = df[url_col]
    y = df['target']
    
    X_train_val, X_test, y_train_val, y_test = train_test_split(X, y, test_size=0.15, random_state=42, stratify=y)
    X_train, X_val, y_train, y_val = train_test_split(X_train_val, y_train_val, test_size=0.1765, random_state=42, stratify=y_train_val)
    
    from sklearn.decomposition import PCA
    
    # Pipeline
    struct_pipeline = Pipeline([
        ('extractor', FunctionTransformer(extract_url_features, validate=False)),
        ('scaler', StandardScaler()),
        ('pca', PCA(n_components=0.95, random_state=42)) # keep 95% variance
    ])
    
    clf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, class_weight='balanced')
    
    full_pipeline = Pipeline([
        ('features', struct_pipeline),
        ('classifier', clf)
    ])
    
    print("Training Random Forest with PCA for URLs...")
    full_pipeline.fit(X_train, y_train)
    
    # Plot PCA 2D representation for visualization.
    # Uses the ALREADY-FITTED preprocessing (transform only — the fitted
    # production pipeline is never refit here). The classifier does not
    # depend on this visualization in any way.
    X_train_pca = struct_pipeline.transform(X_train)
    if X_train_pca.shape[1] >= 2:
        plt.figure(figsize=(8, 6))
        scatter = plt.scatter(X_train_pca[:, 0], X_train_pca[:, 1], c=y_train, cmap='coolwarm', alpha=0.5)
        plt.colorbar(scatter, label='Phishing (1) vs Benign (0)')
        plt.title('PCA 2D Representation of URL Features')
        plt.xlabel('Principal Component 1')
        plt.ylabel('Principal Component 2')
        plt.savefig(os.path.join(FIG_DIR, 'url_pca_scatter.png'))
        plt.close()
    else:
        print(f"PCA visualization skipped: only {X_train_pca.shape[1]} component(s) "
              "available (need at least 2 for a 2D scatter).")
    
    # Evaluate
    print("Evaluating on UNTOUCHED TEST SET...")
    y_test_pred = full_pipeline.predict(X_test)
    y_test_prob = full_pipeline.predict_proba(X_test)[:, 1]
    
    acc = accuracy_score(y_test, y_test_pred)
    prec = precision_score(y_test, y_test_pred)
    rec = recall_score(y_test, y_test_pred)
    f1 = f1_score(y_test, y_test_pred)
    roc_auc = roc_auc_score(y_test, y_test_prob)
    
    print(f"Test Accuracy: {acc:.4f}")
    print(f"Test F1: {f1:.4f}")
    
    cm = confusion_matrix(y_test, y_test_pred)
    tn, fp, fn, tp = cm.ravel()
    
    plt.figure(figsize=(6, 4))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Reds')
    plt.title('URL Model Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.savefig(os.path.join(FIG_DIR, 'url_confusion_matrix.png'))
    plt.close()

    # Save Model (directories were created at the start of training)
    print("Saving URL model...")
    model_dir = URL_MODEL_DIR
    meta_dir = META_DIR
    joblib.dump(full_pipeline, os.path.join(model_dir, "final_url_model.joblib"))
    
    metadata = {
        "model_version": "1.0",
        "training_date": datetime.now().isoformat(),
        "dataset": "data/raw/urldata.csv (Domain + Label columns; 0=Benign, 1=Phishing)",
        "classes": ["Benign", "Phishing/Malicious"],
        "metrics": {
            "test_accuracy": acc,
            "test_precision": prec,
            "test_recall": rec,
            "test_f1": f1,
            "test_roc_auc": roc_auc,
            "false_positive_rate": fp / (fp + tn),
            "false_negative_rate": fn / (fn + tp)
        }
    }
    with open(os.path.join(meta_dir, "url_model_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=4)
        
    print("URL model training complete.")

if __name__ == "__main__":
    train_url_model()
