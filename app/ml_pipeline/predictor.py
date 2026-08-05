import os
import numpy as np
from joblib import load
import pandas as pd
from loguru import logger as log

class MLPredictor:
    """
    Clase con carga perezosa (Lazy Loading) de modelos de ML.
    Previene fallos de SIMD/AVX (Illegal Instruction) en CPUs virtuales durante la importación inicial.
    """
    def __init__(self):
        self._models_loaded = False
        self.binary_rf = None
        self.binary_xgb = None
        self.binary_log = None

        self.classify_rf = None
        self.classify_xgb = None
        self.classify_log = None

    def _ensure_models_loaded(self):
        if self._models_loaded:
            return

        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "trained_models"))

        # Cargar modelos RandomForest
        try:
            self.binary_rf = load(os.path.join(base_path, "binary", "random_forest_model.pkl"))
            self.classify_rf = load(os.path.join(base_path, "classify", "random_forest_model.pkl"))
        except Exception as e:
            log.error(f"Error al cargar RandomForest: {e}")

        # Cargar modelos XGBoost
        try:
            self.binary_xgb = load(os.path.join(base_path, "binary", "xgboost_model.pkl"))
            self.classify_xgb = load(os.path.join(base_path, "classify", "xgboost_model.pkl"))
        except Exception as e:
            log.error(f"Error al cargar XGBoost: {e}")

        # Cargar modelos Keras / TensorFlow con importación perezosa
        try:
            from tensorflow.keras.models import load_model
            self.binary_log = load_model(os.path.join(base_path, "binary", "logistic_regression_model.keras"))
            self.classify_log = load_model(os.path.join(base_path, "classify", "logistic_regression_model.keras"))
        except Exception as e:
            log.warning(f"No se pudo cargar modelo Keras (posible incompatibilidad de CPU/AVX en host): {e}")
            self.binary_log = None
            self.classify_log = None

        self._models_loaded = True

    def _get_binary_probabilities(self, model, df: pd.DataFrame, model_type: str):
        """Obtiene probabilidades para modelos binarios."""
        if model is None:
            return np.array([0.5])
        if model_type == "keras":
            probs = model.predict(df, verbose=0)
            return probs.flatten()
        else:
            if hasattr(model, 'predict_proba'):
                probs = model.predict_proba(df)
                return probs[:, 1]
            else:
                return model.predict(df).flatten()

    def _get_multiclass_probabilities(self, model, df: pd.DataFrame, model_type: str):
        """Obtiene probabilidades para modelos multiclase."""
        if model is None:
            return np.zeros((len(df), 3))
        if model_type == "keras":
            probs = model.predict(df, verbose=0)
            return probs
        else:
            if hasattr(model, 'predict_proba'):
                return model.predict_proba(df)
            else:
                preds = model.predict(df)
                n_classes = 3  
                one_hot = np.zeros((len(preds), n_classes))
                for i, pred in enumerate(preds):
                    one_hot[i, int(pred)] = 1.0
                return one_hot

    def predict_binary(self, df: pd.DataFrame) -> dict:
        """Realiza predicciones con el ensamblaje de modelos binarios."""
        self._ensure_models_loaded()
        df_single_row = df.head(1)
        
        valid_probs = []
        rf_pred, xgb_pred, keras_pred = 0, 0, 0

        if self.binary_rf is not None:
            rf_probs = self._get_binary_probabilities(self.binary_rf, df_single_row, "sklearn")
            rf_pred = int(rf_probs[0] > 0.5)
            valid_probs.append(rf_probs[0])

        if self.binary_xgb is not None:
            xgb_probs = self._get_binary_probabilities(self.binary_xgb, df_single_row, "sklearn")
            xgb_pred = int(xgb_probs[0] > 0.5)
            valid_probs.append(xgb_probs[0])

        if self.binary_log is not None:
            keras_probs = self._get_binary_probabilities(self.binary_log, df_single_row, "keras")
            keras_pred = int(keras_probs[0] > 0.5)
            valid_probs.append(keras_probs[0])
        
        ensemble_confidence = float(np.mean(valid_probs)) if valid_probs else 0.5
        
        return {
            "predictions": {
                "Random_Forest": rf_pred,
                "XGBoost": xgb_pred,
                "TensorFlow_Logistic_Regression": keras_pred,
            },
            "probabilities": {
                "Random_Forest_preds": rf_probs.tolist() if self.binary_rf else [],
                "XGBoost_preds": xgb_probs.tolist() if self.binary_xgb else [],
                "TensorFlow_Logistic_Regression_preds": keras_probs.tolist() if self.binary_log else [],
            },
            "ensemble_confidence": ensemble_confidence
        }

    def predict_classify(self, df: pd.DataFrame) -> dict:
        """Realiza predicciones con el ensamblaje de modelos de clasificación."""
        self._ensure_models_loaded()
        df_single_row = df.head(1)
        
        valid_confs = []
        predictions = []

        if self.classify_rf is not None:
            rf_probs = self._get_multiclass_probabilities(self.classify_rf, df_single_row, "sklearn")
            rf_pred = int(np.argmax(rf_probs[0]))
            predictions.append(rf_pred)

        if self.classify_xgb is not None:
            xgb_probs = self._get_multiclass_probabilities(self.classify_xgb, df_single_row, "sklearn")
            xgb_pred = int(np.argmax(xgb_probs[0]))
            predictions.append(xgb_pred)

        if self.classify_log is not None:
            keras_probs = self._get_multiclass_probabilities(self.classify_log, df_single_row, "keras")
            keras_pred = int(np.argmax(keras_probs[0]))
            predictions.append(keras_pred)

        predicted_class = max(set(predictions), key=predictions.count) if predictions else 0

        if self.classify_rf is not None:
            valid_confs.append(rf_probs[0][predicted_class])
        if self.classify_xgb is not None:
            valid_confs.append(xgb_probs[0][predicted_class])
        if self.classify_log is not None:
            valid_confs.append(keras_probs[0][predicted_class])

        ensemble_confidence = float(np.mean(valid_confs)) if valid_confs else 0.5
        
        return {
            "predictions": {
                "Random_Forest": predictions[0] if len(predictions) > 0 else 0,
                "XGBoost": predictions[1] if len(predictions) > 1 else 0,
                "TensorFlow_Logistic_Regression": predictions[2] if len(predictions) > 2 else 0,
            },
            "probabilities": {
                "Random_Forest_preds": rf_probs.tolist() if self.classify_rf else [],
                "XGBoost_preds": xgb_probs.tolist() if self.classify_xgb else [],
                "TensorFlow_Logistic_Regression_preds": keras_probs.tolist() if self.classify_log else [],
            },
            "predicted_class": predicted_class,
            "ensemble_confidence": ensemble_confidence
        }

ml_predictor = MLPredictor()