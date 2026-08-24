import os
import sys
import pandas as pd
import numpy as np
import joblib
import logging
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.infrastructure.ml.classify import classify_logistic_regression, classify_random_forest, classify_xgboost

def run_pipeline():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    dataset_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "noteboks", "split", "train_classify.csv"))
    test_dataset_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "noteboks", "split", "test_data", "test_classify.csv"))
    
    logging.info(f"Loading multiclass train dataset from: {dataset_path}")
    logging.info(f"Loading multiclass test dataset from: {test_dataset_path}")
    
    df_train = pd.read_csv(dataset_path)
    df_test = pd.read_csv(test_dataset_path)
    
    exclude_columns = ['label', 'gesture', 'gb_score', 'is_synthetic']
    feature_columns = [col for col in df_train.columns if col not in exclude_columns]
    
    X_train = df_train[feature_columns].values
    y_raw_train = df_train['gb_score'].values
    train_y_min = np.min(y_raw_train)
    y_train = y_raw_train - train_y_min
    
    X_test = df_test[feature_columns].values
    y_raw_test = df_test['gb_score'].values
    y_test = y_raw_test - train_y_min
    
    logging.info(f"Features mapped dynamically: {len(feature_columns)}")
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    base_output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "trained_models", "v2.0", "classify"))
    
    # Save Scaler
    joblib.dump(scaler, os.path.join(base_output_dir, "scaler", "scaler.pkl"))
    
    logging.info("Training Logistic Regression...")
    keras_model = classify_logistic_regression.create_model(input_dim=X_train_scaled.shape[1])
    keras_model.fit(X_train_scaled, y_train, epochs=50, batch_size=32, validation_data=(X_test_scaled, y_test), verbose=1)
    keras_model.save(os.path.join(base_output_dir, "models", "logistic_regression_model.keras"))
    
    logging.info("Training Random Forest...")
    rf_model = classify_random_forest.create_model()
    rf_model.fit(X_train_scaled, y_train)
    joblib.dump(rf_model, os.path.join(base_output_dir, "models", "random_forest_model.pkl"))
    rf_preds = rf_model.predict(X_test_scaled)
    
    logging.info("Training XGBoost...")
    xgb_model = classify_xgboost.create_model()
    xgb_model.fit(X_train_scaled, y_train)
    joblib.dump(xgb_model, os.path.join(base_output_dir, "models", "xgboost_model.pkl"))
    
    generate_plots(y_test, rf_preds, os.path.join(base_output_dir, "metrics"), rf_model, xgb_model, feature_columns)

def generate_plots(y_true, rf_preds, output_dir, rf_model, xgb_model, feature_columns):
    # Multiclass Confusion Matrix
    cm = confusion_matrix(y_true, rf_preds)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm)
    disp.plot(cmap=plt.cm.Blues)
    plt.title("Multiclass Confusion Matrix (Random Forest)")
    plt.savefig(os.path.join(output_dir, "confusion_matrix.png"))
    plt.close()
    
    # Feature Importance (Random Forest)
    if hasattr(rf_model, 'feature_importances_'):
        importances = rf_model.feature_importances_
        indices = np.argsort(importances)[-15:] # Top 15 features
        plt.figure(figsize=(12, 8))
        plt.title('Top 15 Feature Importances (Random Forest)')
        plt.barh(range(len(indices)), importances[indices], align='center', color='skyblue')
        plt.yticks(range(len(indices)), [feature_columns[i] for i in indices])
        plt.xlabel('Relative Importance')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "feature_importance_rf.png"))
        plt.close()
        
    # Feature Importance (XGBoost)
    if hasattr(xgb_model, 'feature_importances_'):
        importances = xgb_model.feature_importances_
        indices = np.argsort(importances)[-15:] # Top 15 features
        plt.figure(figsize=(12, 8))
        plt.title('Top 15 Feature Importances (XGBoost)')
        plt.barh(range(len(indices)), importances[indices], align='center', color='lightgreen')
        plt.yticks(range(len(indices)), [feature_columns[i] for i in indices])
        plt.xlabel('Relative Importance')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "feature_importance_xgb.png"))
        plt.close()
        
    logging.info("Metrics and plots saved successfully.")

if __name__ == "__main__":
    run_pipeline()
