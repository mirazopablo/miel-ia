import os
import joblib
import pdb
from fastapi import APIRouter, Depends, UploadFile, File
import pandas as pd
import pickle
import numpy as np
import io

from app.infrastructure.db.DTOs.auth_schema import UserOut  
from ...api.v1.auth import get_current_user

test_binary = APIRouter()

def load_models():
    from tensorflow.keras.models import load_model
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..","..","..", "trained_models", "v2.0", "binary"))
    model_path = os.path.join(base_path, "models")
    
    keras_model_path = os.path.join(model_path, "logistic_regression_model.keras")
    rf_model_path = os.path.join(model_path, "random_forest_model.pkl")
    xgb_model_path = os.path.join(model_path, "xgboost_model.pkl")

    print(f"Cargando modelos desde: {base_path}")
    print(f"  - Keras: {keras_model_path}")
    print(f"  - RF: {rf_model_path}")
    print(f"  - XGB: {xgb_model_path}")

    keras_model = load_model(keras_model_path)
    print(f"Modelo Keras cargado: {type(keras_model)}")

    try:
        rf_model = joblib.load(rf_model_path)
        print(f"Modelo RandomForest cargado con joblib: {type(rf_model)}")
    except Exception as e:
        print(f"Error al cargar con joblib: {e}")
        print("Intentando cargar con pickle...")
        with open(rf_model_path, "rb") as f:
            rf_model = pickle.load(f)
            print(f"Modelo RandomForest cargado con pickle: {type(rf_model)}")

    if isinstance(rf_model, np.ndarray):
        raise TypeError("Error: rf_model fue sobrescrito por un array de predicciones en algún punto.")
    
    if not hasattr(rf_model, 'predict'):
        raise TypeError(f"Error: rf_model no parece tener un método 'predict'. Tipo: {type(rf_model)}")
    
    if not hasattr(rf_model, 'predict_proba'):
        print(" Advertencia: rf_model no tiene método 'predict_proba', puede causar errores al usarlo.")

    try:
        xgb_model = joblib.load(xgb_model_path)
        print(f"Modelo XGBoost cargado con joblib: {type(xgb_model)}")
    except Exception as e:
        print(f"Error al cargar XGBoost con joblib: {e}")
        print("Intentando cargar con pickle...")
        with open(xgb_model_path, "rb") as f:
            xgb_model = pickle.load(f)
            print(f"Modelo XGBoost cargado con pickle: {type(xgb_model)}")

    if not hasattr(xgb_model, 'predict'):
        raise TypeError(f"Error: xgb_model no parece tener un método 'predict'. Tipo: {type(xgb_model)}")

    return keras_model, rf_model, xgb_model

@test_binary.post("/test-binary")
async def test_models_endpoint(file: UploadFile = File(...), current_user: UserOut = Depends(get_current_user)):
    try:
        keras_model, rf_model, xgb_model = load_models()
        print("Modelos cargados correctamente")
    except Exception as e:
        print(f"Error al cargar modelos: {e}")
        return {"error": f"Error al cargar modelos: {str(e)}"}

    try:
        content = await file.read()
        df = pd.read_csv(io.StringIO(content.decode("utf-8")))
        print(f"Archivo CSV cargado: {df.shape[0]} filas, {df.shape[1]} columnas")
    except Exception as e:
        print(f"Error al procesar el archivo CSV: {e}")
        return {"error": f"Error al procesar el archivo CSV: {str(e)}"}

    exclude_columns = ['label', 'gesture', 'gb_score', 'is_synthetic']
    feature_columns = [col for col in df.columns if col not in exclude_columns]

    missing_columns = [col for col in feature_columns if col not in df.columns]
    if missing_columns:
        print(f"Columnas faltantes en el CSV: {missing_columns}")
        return {"error": f"Columnas faltantes en el CSV: {', '.join(missing_columns)}"}

    X_raw = df[feature_columns].values
    
    scaler_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..","..","..", "trained_models", "v2.0", "binary", "scaler", "scaler.pkl"))
    try:
        scaler = joblib.load(scaler_path)
        X = scaler.transform(X_raw)
    except Exception as e:
        print(f"Error cargando el scaler: {e}")
        return {"error": f"Error cargando scaler: {str(e)}"}
        
    print(f"Matriz de características preparada y escalada: {X.shape}")

    try:
        keras_predictions = keras_model.predict(X)
        print(f"Predicciones Keras completadas: {keras_predictions.shape}")

        rf_predictions = rf_model.predict_proba(X)[:, 1]
        print(f"Predicciones RandomForest completadas: {rf_predictions.shape}")

        xgb_predictions = xgb_model.predict_proba(X)[:, 1]
        print(f"Predicciones XGBoost completadas: {xgb_predictions.shape}")

        return {
            "keras_preds": keras_predictions.flatten().tolist(),
            "rf_preds": rf_predictions.tolist(),
            "xgb_preds": xgb_predictions.tolist()
        }
    except Exception as e:
        print(f"Error al realizar predicciones: {e}")
        return {"error": f"Error al realizar predicciones: {str(e)}"}