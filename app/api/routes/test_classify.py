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
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..","..","..", "trained_models", "classify"))


    
    keras_model_path = os.path.join(base_path, "logistic_regression_model.keras")
    rf_model_path = os.path.join(base_path, "random_forest_model.pkl")
    xgb_model_path = os.path.join(base_path, "xgboost_model.pkl")

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

    feature_columns = [  
        'standard_deviation_e1', 'standard_deviation_e2', 'standard_deviation_e3', 'standard_deviation_e4',
        'standard_deviation_e5', 'standard_deviation_e6', 'standard_deviation_e7', 'standard_deviation_e8',
        'root_mean_square_e1', 'root_mean_square_e2', 'root_mean_square_e3', 'root_mean_square_e4',
        'root_mean_square_e5', 'root_mean_square_e6', 'root_mean_square_e7', 'root_mean_square_e8',
        'minimum_e1', 'minimum_e2', 'minimum_e3', 'minimum_e4', 'minimum_e5', 'minimum_e6', 'minimum_e7', 'minimum_e8',
        'maximum_e1', 'maximum_e2', 'maximum_e3', 'maximum_e4', 'maximum_e5', 'maximum_e6', 'maximum_e7', 'maximum_e8',
        'zero_crossings_e1', 'zero_crossings_e2', 'zero_crossings_e3', 'zero_crossings_e4',
        'zero_crossings_e5', 'zero_crossings_e6', 'zero_crossings_e7', 'zero_crossings_e8',
        'average_amplitude_change_e1', 'average_amplitude_change_e2', 'average_amplitude_change_e3',
        'average_amplitude_change_e4', 'average_amplitude_change_e5', 'average_amplitude_change_e6',
        'average_amplitude_change_e7', 'average_amplitude_change_e8',
        'amplitude_first_burst_e1', 'amplitude_first_burst_e2', 'amplitude_first_burst_e3',
        'amplitude_first_burst_e4', 'amplitude_first_burst_e5', 'amplitude_first_burst_e6',
        'amplitude_first_burst_e7', 'amplitude_first_burst_e8',
        'mean_absolute_value_e1', 'mean_absolute_value_e2', 'mean_absolute_value_e3', 'mean_absolute_value_e4',
        'mean_absolute_value_e5', 'mean_absolute_value_e6', 'mean_absolute_value_e7', 'mean_absolute_value_e8',
        'wave_form_length_e1', 'wave_form_length_e2', 'wave_form_length_e3', 'wave_form_length_e4',
        'wave_form_length_e5', 'wave_form_length_e6', 'wave_form_length_e7', 'wave_form_length_e8',
        'willison_amplitude_e1', 'willison_amplitude_e2', 'willison_amplitude_e3', 'willison_amplitude_e4',
        'willison_amplitude_e5', 'willison_amplitude_e6', 'willison_amplitude_e7', 'willison_amplitude_e8'
    ]

    missing_columns = [col for col in feature_columns if col not in df.columns]
    if missing_columns:
        return {"error": f"Columnas faltantes en el CSV: {', '.join(missing_columns)}"}

    X = df[feature_columns].values

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
