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
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.infrastructure.ml.classify import classify_logistic_regression, classify_random_forest, classify_xgboost

def run_pipeline():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    dataset_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "noteboks", "split", "train_classify.csv"))
    logging.info(f"Loading multiclass dataset from: {dataset_path}")
    
    df = pd.read_csv(dataset_path)
    
    exclude_columns = ['label', 'gesture', 'gb_score', 'is_synthetic']
    feature_columns = [col for col in df.columns if col not in exclude_columns]
    
    X = df[feature_columns].values
    y_raw = df['gb_score'].values
    
    # Ensure classes are 0-indexed (e.g., 1,2,3 -> 0,1,2) for Sparse Categorical Crossentropy
    y = y_raw - np.min(y_raw)
    
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    
    base_output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "trained_models", "v2.0", "classify"))
    
    # Save Scaler
    joblib.dump(scaler, os.path.join(base_output_dir, "scaler", "scaler.pkl"))
    
    logging.info("Training Logistic Regression...")
    keras_model = classify_logistic_regression.create_model(input_dim=X_train_scaled.shape[1])
    keras_model.fit(X_train_scaled, y_train, epochs=50, batch_size=32, validation_data=(X_val_scaled, y_val), verbose=1)
    keras_model.save(os.path.join(base_output_dir, "models", "logistic_regression_model.keras"))
    
    logging.info("Training Random Forest...")
    rf_model = classify_random_forest.create_model()
    rf_model.fit(X_train_scaled, y_train)
    joblib.dump(rf_model, os.path.join(base_output_dir, "models", "random_forest_model.pkl"))
    rf_preds = rf_model.predict(X_val_scaled)
    
    logging.info("Training XGBoost...")
    xgb_model = classify_xgboost.create_model()
    xgb_model.fit(X_train_scaled, y_train)
    joblib.dump(xgb_model, os.path.join(base_output_dir, "models", "xgboost_model.pkl"))
    
    # Multiclass Confusion Matrix
    cm = confusion_matrix(y_val, rf_preds)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm)
    disp.plot(cmap=plt.cm.Blues)
    plt.title("Multiclass Confusion Matrix (Random Forest)")
    plt.savefig(os.path.join(base_output_dir, "metrics", "confusion_matrix.png"))
    plt.close()
    
    logging.info("Metrics and plots saved successfully.")

if __name__ == "__main__":
    run_pipeline()
