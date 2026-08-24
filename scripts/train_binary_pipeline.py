import os
import sys
import pandas as pd
import numpy as np
import joblib
import logging
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay, roc_curve, auc

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.infrastructure.ml.binary import binary_logistic_regression, binary_random_forest, binary_xgboost

def run_pipeline():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    dataset_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "noteboks", "split", "train_binary.csv"))
    logging.info(f"Loading binary dataset from: {dataset_path}")
    
    df = pd.read_csv(dataset_path)
    
    # Dynamically extract features by ignoring metadata and target columns
    exclude_columns = ['label', 'gesture', 'gb_score', 'is_synthetic']
    feature_columns = [col for col in df.columns if col not in exclude_columns]
    
    X = df[feature_columns].values
    y_raw = df['gb_score'].values
    y = (y_raw > 0).astype(int) # Ensure binary representation
    
    logging.info(f"Features mapped dynamically: {len(feature_columns)}")
    
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    logging.info("Fitting StandardScaler to prevent data leakage...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    
    base_output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "trained_models", "v2.0", "binary"))
    
    # Save Scaler
    scaler_path = os.path.join(base_output_dir, "scaler", "scaler.pkl")
    joblib.dump(scaler, scaler_path)
    logging.info(f"Scaler saved to {scaler_path}")
    
    # Train Models
    logging.info("Training Logistic Regression...")
    keras_model = binary_logistic_regression.create_model(input_dim=X_train_scaled.shape[1])
    keras_model.fit(X_train_scaled, y_train, epochs=50, batch_size=32, validation_data=(X_val_scaled, y_val), verbose=1)
    keras_model.save(os.path.join(base_output_dir, "models", "logistic_regression_model.keras"))
    keras_preds = keras_model.predict(X_val_scaled).flatten()
    
    logging.info("Training Random Forest...")
    rf_model = binary_random_forest.create_model()
    rf_model.fit(X_train_scaled, y_train)
    joblib.dump(rf_model, os.path.join(base_output_dir, "models", "random_forest_model.pkl"))
    rf_preds = rf_model.predict_proba(X_val_scaled)[:, 1]
    
    logging.info("Training XGBoost...")
    xgb_model = binary_xgboost.create_model()
    xgb_model.fit(X_train_scaled, y_train)
    joblib.dump(xgb_model, os.path.join(base_output_dir, "models", "xgboost_model.pkl"))
    xgb_preds = xgb_model.predict_proba(X_val_scaled)[:, 1]
    
    generate_plots(y_val, keras_preds, rf_preds, xgb_preds, os.path.join(base_output_dir, "metrics"))

def generate_plots(y_true, keras_preds, rf_preds, xgb_preds, output_dir):
    # ROC Curve
    plt.figure(figsize=(10, 8))
    for name, preds in [("Logistic Regression", keras_preds), ("Random Forest", rf_preds), ("XGBoost", xgb_preds)]:
        fpr, tpr, _ = roc_curve(y_true, preds)
        plt.plot(fpr, tpr, lw=2, label=f'{name} (AUC = {auc(fpr, tpr):.2f})')
        
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Binary ROC Curve')
    plt.legend(loc="lower right")
    plt.savefig(os.path.join(output_dir, "roc_curve.png"))
    plt.close()
    
    # Confusion Matrix (Random Forest)
    rf_binary_preds = (rf_preds > 0.5).astype(int)
    cm = confusion_matrix(y_true, rf_binary_preds)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm)
    disp.plot(cmap=plt.cm.Blues)
    plt.title("Confusion Matrix (Random Forest)")
    plt.savefig(os.path.join(output_dir, "confusion_matrix.png"))
    plt.close()
    logging.info("Metrics and plots saved successfully.")

if __name__ == "__main__":
    run_pipeline()
