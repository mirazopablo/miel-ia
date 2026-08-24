import os
import joblib
from fastapi import APIRouter, Depends, UploadFile, File
import pandas as pd
import pickle
import numpy as np
import io

from app.infrastructure.db.DTOs.auth_schema import UserOut
from ...api.v1.auth import get_current_user

test_classify = APIRouter()

def load_models():
    from tensorflow.keras.models import load_model
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..","..","..", "trained_models", "v2.0", "classify"))
    model_path = os.path.join(base_path, "models")
    
    keras_model_path = os.path.join(model_path, "logistic_regression_model.keras")
    rf_model_path = os.path.join(model_path, "random_forest_model.pkl")
    xgb_model_path = os.path.join(model_path, "xgboost_model.pkl")

    print(f"Cargando modelos desde: {base_path}")

    keras_model = load_model(keras_model_path)
    print(f"Modelo Keras cargado: {type(keras_model)}")

    rf_model = joblib.load(rf_model_path)
    print(f"Modelo RandomForest cargado: {type(rf_model)}")

    xgb_model = joblib.load(xgb_model_path)
    print(f"Modelo XGBoost cargado: {type(xgb_model)}")

    return keras_model, rf_model, xgb_model

@test_classify.post("/test-classify")
async def test_models_endpoint(file: UploadFile = File(...), current_user: UserOut = Depends(get_current_user)):
    try:
        keras_model, rf_model, xgb_model = load_models()
    except Exception as e:
        return {"error": f"Error al cargar modelos: {str(e)}"}

    try:
        content = await file.read()
        df = pd.read_csv(io.StringIO(content.decode("utf-8")))
    except Exception as e:
        return {"error": f"Error al procesar el archivo CSV: {str(e)}"}

    exclude_columns = ['label', 'gesture', 'gb_score', 'is_synthetic']
    feature_columns = [col for col in df.columns if col not in exclude_columns]

    missing_columns = [col for col in feature_columns if col not in df.columns]
    if missing_columns:
        return {"error": f"Columnas faltantes en el CSV: {', '.join(missing_columns)}"}

    X_raw = df[feature_columns].values
    
    scaler_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..","..","..", "trained_models", "v2.0", "classify", "scaler", "scaler.pkl"))
    try:
        scaler = joblib.load(scaler_path)
        X = scaler.transform(X_raw)
    except Exception as e:
        return {"error": f"Error cargando scaler: {str(e)}"}

    try:
        keras_predictions = keras_model.predict(X)
        rf_predictions = rf_model.predict_proba(X)
        xgb_predictions = xgb_model.predict_proba(X)

        return {
            "keras_preds": keras_predictions.tolist(),  
            "rf_preds": rf_predictions.tolist(),        
            "xgb_preds": xgb_predictions.tolist()       
        }
    except Exception as e:
        return {"error": f"Error al realizar predicciones: {str(e)}"}
