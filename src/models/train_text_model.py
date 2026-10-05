import pandas as pd
import numpy as np
import os
import joblib
import json
from datetime import datetime
from sklearn.model_selection import train_test_split, StratifiedKFold, RandomizedSearchCV
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler, FunctionTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import LinearSVC
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score, 
                             roc_auc_score, confusion_matrix, classification_report)
from sklearn.decomposition import TruncatedSVD
import matplotlib
matplotlib.use("Agg")  # headless-safe figure generation
import matplotlib.pyplot as plt
import seaborn as sns
import re

import warnings
warnings.filterwarnings("ignore")

from src.features.text_features import extract_text_features

FIG_DIR = os.path.join("reports", "figures")
TEXT_MODEL_DIR = os.path.join("models", "text")
META_DIR = os.path.join("models", "metadata")

def clean_text(text):
    text = str(text).lower()
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def train_text_model():
    print("Loading SMS Spam dataset...")
    os.makedirs(FIG_DIR, exist_ok=True)
    os.makedirs(TEXT_MODEL_DIR, exist_ok=True)
    os.makedirs(META_DIR, exist_ok=True)
    data_path = os.path.join("data", "raw", "SMSSpamCollection")
    df = pd.read_csv(data_path, sep='\t', header=None, names=['label', 'text'])
    
    print(f"Original shape: {df.shape}")
    df = df.drop_duplicates().reset_index(drop=True)
    print(f"Shape after duplicate removal: {df.shape}")
    
    # Map labels: ham -> 0 (Benign), spam -> 1 (Phishing/Scam)
    df['target'] = df['label'].map({'ham': 0, 'spam': 1})
    df['text_clean'] = df['text'].apply(clean_text)
    
    print(f"Class distribution:\n{df['target'].value_counts(normalize=True)}")
    
    # Split: 70% Train, 15% Val, 15% Test
    X = df['text_clean']
    y = df['target']
    
    X_train_val, X_test, y_train_val, y_test = train_test_split(X, y, test_size=0.15, random_state=42, stratify=y)
    X_train, X_val, y_train, y_val = train_test_split(X_train_val, y_train_val, test_size=0.1765, random_state=42, stratify=y_train_val)
    
    print(f"Train size: {len(X_train)}, Val size: {len(X_val)}, Test size: {len(X_test)}")
    
    # Build a FeatureUnion pipeline
    text_pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.9, sublinear_tf=True)),
        ('svd', TruncatedSVD(n_components=100, random_state=42))
    ])
    
    struct_pipeline = Pipeline([
        ('extractor', FunctionTransformer(extract_text_features, validate=False)),
        ('scaler', StandardScaler())
    ])
    
    features = FeatureUnion([
        ('text', text_pipeline),
        ('struct', struct_pipeline)
    ])
    
    # Train baseline Logistic Regression
    print("Training Logistic Regression...")
    clf = LogisticRegression(class_weight='balanced', random_state=42, max_iter=1000)
    
    full_pipeline = Pipeline([
        ('features', features),
        ('classifier', clf)
    ])
    
    full_pipeline.fit(X_train, y_train)
    
    # Plot SVD 2D representation for visualization.
    # Uses the ALREADY-FITTED pipeline (transform only — never refit here).
    X_train_features = features.transform(X_train)
    # The text pipeline is the first one in FeatureUnion, and SVD outputs 100 components.
    # We take the first two for a 2D scatter plot (kept separate from the production model).
    if X_train_features.shape[1] >= 2:
        plt.figure(figsize=(8, 6))
        # The SVD components are the first 100 columns
        scatter = plt.scatter(X_train_features[:, 0], X_train_features[:, 1], c=y_train, cmap='coolwarm', alpha=0.5)
        plt.colorbar(scatter, label='Phishing/Scam (1) vs Benign (0)')
        plt.title('PCA (SVD) 2D Representation of Text Features')
        plt.xlabel('Principal Component 1')
        plt.ylabel('Principal Component 2')
        plt.savefig(os.path.join(FIG_DIR, 'text_pca_scatter.png'))
        plt.close()
    else:
        print("SVD visualization skipped: fewer than 2 components available.")
    
    # Evaluate on validation
    y_val_pred = full_pipeline.predict(X_val)
    y_val_prob = full_pipeline.predict_proba(X_val)[:, 1]
    
    print("Validation Results:")
    print(f"Accuracy: {accuracy_score(y_val, y_val_pred):.4f}")
    print(f"F1-Score: {f1_score(y_val, y_val_pred):.4f}")
    
    # Evaluate on final test
    print("Evaluating on UNTOUCHED TEST SET...")
    y_test_pred = full_pipeline.predict(X_test)
    y_test_prob = full_pipeline.predict_proba(X_test)[:, 1]
    
    acc = accuracy_score(y_test, y_test_pred)
    prec = precision_score(y_test, y_test_pred)
    rec = recall_score(y_test, y_test_pred)
    f1 = f1_score(y_test, y_test_pred)
    roc_auc = roc_auc_score(y_test, y_test_prob)
    
    print(f"Test Accuracy: {acc:.4f}")
    print(f"Test Precision: {prec:.4f}")
    print(f"Test Recall: {rec:.4f}")
    print(f"Test F1: {f1:.4f}")
    print(f"Test ROC-AUC: {roc_auc:.4f}")
    
    cm = confusion_matrix(y_test, y_test_pred)
    tn, fp, fn, tp = cm.ravel()
    print(f"Confusion Matrix: TN={tn}, FP={fp}, FN={fn}, TP={tp}")
    
    # Save Confusion Matrix figure
    os.makedirs(FIG_DIR, exist_ok=True)
    plt.figure(figsize=(6, 4))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
    plt.title('Text Model Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.savefig(os.path.join(FIG_DIR, 'text_confusion_matrix.png'))
    plt.close()

    # Save Model (directories created first — never rely on manual setup)
    print("Saving model and metadata...")
    os.makedirs(TEXT_MODEL_DIR, exist_ok=True)
    os.makedirs(META_DIR, exist_ok=True)
    model_dir = TEXT_MODEL_DIR
    meta_dir = META_DIR
    joblib.dump(full_pipeline, os.path.join(model_dir, "final_text_model.joblib"))
    
    metadata = {
        "model_version": "1.0",
        "training_date": datetime.now().isoformat(),
        "dataset": "SMS Spam Collection",
        "classes": ["Benign", "Phishing/Scam"],
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
    with open(os.path.join(meta_dir, "text_model_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=4)
        
    print("Text model training complete.")

if __name__ == "__main__":
    train_text_model()
