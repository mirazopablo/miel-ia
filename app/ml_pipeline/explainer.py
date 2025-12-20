# app/ml_pipeline/explainer.py
import pandas as pd
import numpy as np
import shap
from typing import Dict, List, Any, Optional
import warnings

warnings.filterwarnings('ignore')


class MLExplainer:
    """
    Sistema de explicabilidad usando SHAP para modelos de ML.
    Proporciona interpretaciones de las predicciones de los modelos.
    """

    def __init__(self):
        """Inicializa el explicador cargando estadísticas de referencia."""
        try:
            from .predictor import ml_predictor
            self.predictor = ml_predictor
            self.reference_stats = self._load_reference_stats()
        except Exception as e:
            raise RuntimeError(f"MLExplainer initialization error: {e}")
        

    def _load_reference_stats(self) -> Dict[str, Dict[str, float]]:
        """Carga estadísticas de referencia para interpretar valores de características."""
        return {
            'standard_deviation_e1': {'mean': 0.2895, 'std': 0.2465, 'normal_min': 0.0215, 'normal_max': 0.9346},
            'standard_deviation_e2': {'mean': 0.3072, 'std': 0.2446, 'normal_min': 0.0180, 'normal_max': 0.9372},
            'standard_deviation_e3': {'mean': 0.3205, 'std': 0.2454, 'normal_min': 0.0171, 'normal_max': 0.9363},
            'standard_deviation_e4': {'mean': 0.3082, 'std': 0.2465, 'normal_min': 0.0253, 'normal_max': 0.9373},
            'standard_deviation_e5': {'mean': 0.2971, 'std': 0.2494, 'normal_min': 0.0258, 'normal_max': 0.9344},
            'standard_deviation_e6': {'mean': 0.2818, 'std': 0.2582, 'normal_min': 0.0088, 'normal_max': 0.9338},
            'standard_deviation_e7': {'mean': 0.3042, 'std': 0.2549, 'normal_min': 0.0061, 'normal_max': 0.9356},
            'standard_deviation_e8': {'mean': 0.2942, 'std': 0.2593, 'normal_min': 0.0095, 'normal_max': 0.9354},
            'root_mean_square_e1': {'mean': 0.3916, 'std': 0.3201, 'normal_min': 0.0229, 'normal_max': 0.9342},
            'root_mean_square_e2': {'mean': 0.4014, 'std': 0.3135, 'normal_min': 0.0184, 'normal_max': 0.9371},
            'root_mean_square_e3': {'mean': 0.4115, 'std': 0.3124, 'normal_min': 0.0175, 'normal_max': 0.9351},
            'root_mean_square_e4': {'mean': 0.4025, 'std': 0.3134, 'normal_min': 0.0279, 'normal_max': 0.9330},
            'root_mean_square_e5': {'mean': 0.3915, 'std': 0.3156, 'normal_min': 0.0301, 'normal_max': 0.9355},
            'root_mean_square_e6': {'mean': 0.3734, 'std': 0.3304, 'normal_min': 0.0098, 'normal_max': 0.9338},
            'root_mean_square_e7': {'mean': 0.4013, 'std': 0.3226, 'normal_min': 0.0064, 'normal_max': 0.9355},
            'root_mean_square_e8': {'mean': 0.3851, 'std': 0.3288, 'normal_min': 0.0095, 'normal_max': 0.9353},
            'minimum_e1': {'mean': -0.4762, 'std': 0.3220, 'normal_min': -0.9752, 'normal_max': -0.0079},
            'minimum_e2': {'mean': -0.4146, 'std': 0.3222, 'normal_min': -0.9435, 'normal_max': -0.0079},
            'minimum_e3': {'mean': -0.4146, 'std': 0.3222, 'normal_min': -0.9435, 'normal_max': -0.0079},
            'minimum_e4': {'mean': -0.4146, 'std': 0.3222, 'normal_min': -0.9435, 'normal_max': -0.0079},
            'minimum_e5': {'mean': -0.4146, 'std': 0.3222, 'normal_min': -0.9435, 'normal_max': -0.0079},
            'minimum_e6': {'mean': -0.4146, 'std': 0.3222, 'normal_min': -0.9435, 'normal_max': -0.0079},
            'minimum_e7': {'mean': -0.4146, 'std': 0.3222, 'normal_min': -0.9435, 'normal_max': -0.0079},
            'minimum_e8': {'mean': -0.4146, 'std': 0.3222, 'normal_min': -0.9435, 'normal_max': -0.0079},
            'maximum_e1': {'mean': 0.4762, 'std': 0.3220, 'normal_min': 0.0079, 'normal_max': 0.9752},
            'maximum_e2': {'mean': 0.4146, 'std': 0.3222, 'normal_min': 0.0079, 'normal_max': 0.9435},
            'maximum_e3': {'mean': 0.4146, 'std': 0.3222, 'normal_min': 0.0079, 'normal_max': 0.9435},
            'maximum_e4': {'mean': 0.4146, 'std': 0.3222, 'normal_min': 0.0079, 'normal_max': 0.9435},
            'maximum_e5': {'mean': 0.4146, 'std': 0.3222, 'normal_min': 0.0079, 'normal_max': 0.9435},
            'maximum_e6': {'mean': 0.4146, 'std': 0.3222, 'normal_min': 0.0079, 'normal_max': 0.9435},
            'maximum_e7': {'mean': 0.4146, 'std': 0.3222, 'normal_min': 0.0079, 'normal_max': 0.9435},
            'maximum_e8': {'mean': 0.4146, 'std': 0.3222, 'normal_min': 0.0079, 'normal_max': 0.9435},
            'zero_crossings_e1': {'mean': 0.5361, 'std': 0.2403, 'normal_min': 0.1111, 'normal_max': 0.9332},
            'zero_crossings_e2': {'mean': 0.5725, 'std': 0.2370, 'normal_min': 0.1175, 'normal_max': 0.9378},
            'zero_crossings_e3': {'mean': 0.5954, 'std': 0.2454, 'normal_min': 0.1068, 'normal_max': 0.9384},
            'zero_crossings_e4': {'mean': 0.5441, 'std': 0.2429, 'normal_min': 0.1143, 'normal_max': 0.9349},
            'zero_crossings_e5': {'mean': 0.5329, 'std': 0.2439, 'normal_min': 0.1183, 'normal_max': 0.9358},
            'zero_crossings_e6': {'mean': 0.5471, 'std': 0.2425, 'normal_min': 0.1010, 'normal_max': 0.9383},
            'zero_crossings_e7': {'mean': 0.5440, 'std': 0.2536, 'normal_min': 0.0866, 'normal_max': 0.9339},
            'zero_crossings_e8': {'mean': 0.5246, 'std': 0.2558, 'normal_min': 0.0952, 'normal_max': 0.9340},
            'average_amplitude_change_e1': {'mean': 0.3790, 'std': 0.3208, 'normal_min': 0.0209, 'normal_max': 0.9345},
            'average_amplitude_change_e2': {'mean': 0.4006, 'std': 0.3100, 'normal_min': 0.0183, 'normal_max': 0.9294},
            'average_amplitude_change_e3': {'mean': 0.4142, 'std': 0.3108, 'normal_min': 0.0170, 'normal_max': 0.9342},
            'average_amplitude_change_e4': {'mean': 0.3966, 'std': 0.3134, 'normal_min': 0.0278, 'normal_max': 0.9353},
            'average_amplitude_change_e5': {'mean': 0.3882, 'std': 0.3147, 'normal_min': 0.0294, 'normal_max': 0.9315},
            'average_amplitude_change_e6': {'mean': 0.3738, 'std': 0.3257, 'normal_min': 0.0120, 'normal_max': 0.9338},
            'average_amplitude_change_e7': {'mean': 0.4072, 'std': 0.3163, 'normal_min': 0.0070, 'normal_max': 0.9354},
            'average_amplitude_change_e8': {'mean': 0.3863, 'std': 0.3277, 'normal_min': 0.0098, 'normal_max': 0.9353},
            'amplitude_first_burst_e1': {'mean': 0.3668, 'std': 0.3340, 'normal_min': 0.0150, 'normal_max': 0.9326},
            'amplitude_first_burst_e2': {'mean': 0.3764, 'std': 0.3248, 'normal_min': 0.0153, 'normal_max': 0.9316},
            'amplitude_first_burst_e3': {'mean': 0.3836, 'std': 0.3233, 'normal_min': 0.0164, 'normal_max': 0.9327},
            'amplitude_first_burst_e4': {'mean': 0.3854, 'std': 0.3216, 'normal_min': 0.0233, 'normal_max': 0.9369},
            'amplitude_first_burst_e5': {'mean': 0.3701, 'std': 0.3329, 'normal_min': 0.0244, 'normal_max': 0.9343},
            'amplitude_first_burst_e6': {'mean': 0.3578, 'std': 0.3378, 'normal_min': 0.0139, 'normal_max': 0.9318},
            'amplitude_first_burst_e7': {'mean': 0.3679, 'std': 0.3378, 'normal_min': 0.0081, 'normal_max': 0.9326},
            'amplitude_first_burst_e8': {'mean': 0.3658, 'std': 0.3400, 'normal_min': 0.0110, 'normal_max': 0.9340},
            'mean_absolute_value_e1': {'mean': 0.3835, 'std': 0.3219, 'normal_min': 0.0221, 'normal_max': 0.9343},
            'mean_absolute_value_e2': {'mean': 0.3941, 'std': 0.3153, 'normal_min': 0.0160, 'normal_max': 0.9360},
            'mean_absolute_value_e3': {'mean': 0.4049, 'std': 0.3123, 'normal_min': 0.0145, 'normal_max': 0.9352},
            'mean_absolute_value_e4': {'mean': 0.3996, 'std': 0.3137, 'normal_min': 0.0279, 'normal_max': 0.9331},
            'mean_absolute_value_e5': {'mean': 0.3895, 'std': 0.3162, 'normal_min': 0.0301, 'normal_max': 0.9354},
            'mean_absolute_value_e6': {'mean': 0.3724, 'std': 0.3304, 'normal_min': 0.0098, 'normal_max': 0.9337},
            'mean_absolute_value_e7': {'mean': 0.3981, 'std': 0.3227, 'normal_min': 0.0064, 'normal_max': 0.9355},
            'mean_absolute_value_e8': {'mean': 0.3830, 'std': 0.3288, 'normal_min': 0.0095, 'normal_max': 0.9353},
            'wave_form_length_e1': {'mean': 0.3796, 'std': 0.3214, 'normal_min': 0.0209, 'normal_max': 0.9351},
            'wave_form_length_e2': {'mean': 0.3942, 'std': 0.3123, 'normal_min': 0.0168, 'normal_max': 0.9349},
            'wave_form_length_e3': {'mean': 0.4075, 'std': 0.3148, 'normal_min': 0.0145, 'normal_max': 0.9343},
            'wave_form_length_e4': {'mean': 0.3963, 'std': 0.3140, 'normal_min': 0.0253, 'normal_max': 0.9330},
            'wave_form_length_e5': {'mean': 0.3869, 'std': 0.3157, 'normal_min': 0.0295, 'normal_max': 0.9348},
            'wave_form_length_e6': {'mean': 0.3718, 'std': 0.3271, 'normal_min': 0.0100, 'normal_max': 0.9327},
            'wave_form_length_e7': {'mean': 0.4001, 'std': 0.3205, 'normal_min': 0.0060, 'normal_max': 0.9339},
            'wave_form_length_e8': {'mean': 0.3818, 'std': 0.3277, 'normal_min': 0.0089, 'normal_max': 0.9320},
            'willison_amplitude_e1': {'mean': 0.3980, 'std': 0.3240, 'normal_min': 0.0, 'normal_max': 0.9381},
            'willison_amplitude_e2': {'mean': 0.4512, 'std': 0.2973, 'normal_min': 0.0, 'normal_max': 0.9359},
            'willison_amplitude_e3': {'mean': 0.4836, 'std': 0.2914, 'normal_min': 0.0, 'normal_max': 0.9352},
            'willison_amplitude_e4': {'mean': 0.3931, 'std': 0.3249, 'normal_min': 0.0, 'normal_max': 0.9296},
            'willison_amplitude_e5': {'mean': 0.3718, 'std': 0.3382, 'normal_min': 0.0, 'normal_max': 0.9347},
            'willison_amplitude_e6': {'mean': 0.4083, 'std': 0.3162, 'normal_min': 0.0, 'normal_max': 0.9348},
            'willison_amplitude_e7': {'mean': 0.4678, 'std': 0.3099, 'normal_min': 0.0, 'normal_max': 0.9371},
            'willison_amplitude_e8': {'mean': 0.4176, 'std': 0.3260, 'normal_min': 0.0, 'normal_max': 0.9328},
        }

    def explain_binary_prediction(self, df: pd.DataFrame, predictions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Explica las predicciones de los modelos binarios usando SHAP."""
        explanations = []

        if 'predictions' in predictions:
            pred_dict = predictions['predictions']
        else:
            pred_dict = predictions

        try:
            rf_explanation = self._explain_model(
                self.predictor.binary_rf, df, "Random Forest",
                pred_dict.get("Random_Forest", 0), "binary"
            )
            explanations.append(rf_explanation)

            xgb_explanation = self._explain_model(
                self.predictor.binary_xgb, df, "XGBoost",
                pred_dict.get("XGBoost", 0), "binary"
            )
            explanations.append(xgb_explanation)

            keras_explanation = self._explain_keras_model(
                df, "TensorFlow Logistic Regression",
                pred_dict.get("TensorFlow_Logistic_Regression", 0), "binary"
            )
            explanations.append(keras_explanation)

        except Exception as e:
            raise RuntimeError(f"Binary explanation error: {e}")

        return explanations

    def explain_classification_prediction(self, df: pd.DataFrame, predictions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Explica las predicciones de los modelos de clasificación usando SHAP."""
        explanations = []

        if 'predictions' in predictions:
            pred_dict = predictions['predictions']
        else:
            pred_dict = predictions

        try:
            rf_explanation = self._explain_model(
                self.predictor.classify_rf, df, "Random Forest",
                pred_dict.get("Random_Forest", 0), "classification"
            )
            explanations.append(rf_explanation)

            xgb_explanation = self._explain_model(
                self.predictor.classify_xgb, df, "XGBoost",
                pred_dict.get("XGBoost", 0), "classification"
            )
            explanations.append(xgb_explanation)

            keras_explanation = self._explain_keras_model(
                df, "TensorFlow Logistic Regression",
                pred_dict.get("TensorFlow_Logistic_Regression", 0), "classification"
            )
            explanations.append(keras_explanation)

        except Exception as e:
            raise RuntimeError(f"Classification explanation error: {e}")

        return explanations

    def _explain_model(self, model, df: pd.DataFrame, model_name: str,
                       prediction: int, task_type: str) -> Dict[str, Any]:
        """Explica un modelo individual usando SHAP."""
        try:
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(df)

            if isinstance(shap_values, list):
                if len(shap_values) > prediction:
                    shap_values = shap_values[prediction]
                else:
                    shap_values = shap_values[0]

            if shap_values.ndim > 1:
                shap_values = shap_values[0]

            feature_importance = self._get_feature_importance(df, shap_values)

            return {
                "model_name": model_name,
                "prediction": prediction,
                "task_type": task_type,
                "top_features": feature_importance[:10], 
                "explanation_summary": self._generate_explanation_summary(
                    feature_importance, prediction, task_type
                )
            }

        except Exception as e:
            raise RuntimeError(f"Model explanation error - model failed: {model_name}: {e}")
            return {
                "model_name": model_name,
                "prediction": prediction,
                "task_type": task_type,
                "error": str(e),
                "top_features": [],
                "explanation_summary": f"No se pudo generar explicación para {model_name}"
            }

    def _explain_keras_model(self, df: pd.DataFrame, model_name: str,
                             prediction: int, task_type: str) -> Dict[str, Any]:
        """Explicación simplificada para modelos de Keras."""
        try:
            feature_importance = []

            for feature in df.columns:
                value = df[feature].iloc[0]
                stats = self.reference_stats.get(feature, {})

                if stats:
                    mean = stats.get('mean', 0)
                    std = stats.get('std', 1)
                    z_score = (value - mean) / std if std > 0 else 0

                    normal_min = stats.get('normal_min', mean - 2 * std)
                    normal_max = stats.get('normal_max', mean + 2 * std)

                    if value < normal_min:
                        status = "below_normal"
                    elif value > normal_max:
                        status = "above_normal"
                    else:
                        status = "normal"

                    feature_importance.append({
                        "feature": feature,
                        "actual_value": float(value),
                        "impact": abs(z_score) * 0.1,  
                        "status": status,
                        "z_score": float(z_score)
                    })

            feature_importance.sort(key=lambda x: abs(x['impact']), reverse=True)

            return {
                "model_name": model_name,
                "prediction": prediction,
                "task_type": task_type,
                "top_features": feature_importance[:10],
                "explanation_summary": f"Análisis estadístico para {model_name}: predicción = {prediction}"
            }

        except Exception as e:
            raise RuntimeError(f"Keras model explanation error: {e}")
            return {
                "model_name": model_name,
                "prediction": prediction,
                "task_type": task_type,
                "error": str(e),
                "top_features": [],
                "explanation_summary": f"No se pudo generar explicación para {model_name}"
            }

    def _get_feature_importance(self, df: pd.DataFrame, shap_values: np.ndarray) -> List[Dict[str, Any]]:
        """Obtiene importancia de características con interpretación de valores."""
        feature_importance = []

        for i, feature in enumerate(df.columns):
            if i < len(shap_values):
                shap_value = float(shap_values[i])
                actual_value = float(df[feature].iloc[0])

                stats = self.reference_stats.get(feature, {})

                z_score = 0
                status = "unknown"

                if stats:
                    mean = stats.get('mean', 0)
                    std = stats.get('std', 1)
                    z_score = (actual_value - mean) / std if std > 0 else 0

                    normal_min = stats.get('normal_min', mean - 2 * std)
                    normal_max = stats.get('normal_max', mean + 2 * std)

                    if actual_value < normal_min:
                        status = "below_normal"
                    elif actual_value > normal_max:
                        status = "above_normal"
                    else:
                        status = "normal"

                electrode = "unknown"
                metric = feature
                if "_e" in feature:
                    parts = feature.split("_e")
                    if len(parts) == 2:
                        metric = parts[0]
                        electrode = f"e{parts[1]}"

                feature_importance.append({
                    "feature": feature,
                    "electrode": electrode,
                    "metric": metric,
                    "shap_value": shap_value,
                    "actual_value": actual_value,
                    "impact": abs(shap_value),
                    "direction": "positive" if shap_value > 0 else "negative",
                    "status": status,
                    "z_score": float(z_score)
                })

        feature_importance.sort(key=lambda x: x['impact'], reverse=True)
        return feature_importance

    def _generate_explanation_summary(self, feature_importance: List[Dict[str, Any]],
                                      prediction: int, task_type: str) -> str:
        """Genera un resumen textual de la explicación."""
        if not feature_importance:
            return "No se pudieron identificar factores determinantes."

        top_feature = feature_importance[0]

        if task_type == "binary":
            pred_text = "EMG positivo" if prediction == 1 else "EMG negativo"
        else:
            pred_text = f"Nivel {prediction}"

        summary = f"Predicción: {pred_text}. "
        summary += f"Factor principal: {top_feature['metric']} en {top_feature['electrode']} "
        summary += f"(valor: {top_feature['actual_value']:.3f}, estado: {top_feature['status']})"

        return summary

    def generate_summary_insights(self, binary_explanations: List[Dict[str, Any]],
                                  classify_explanations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Genera insights de resumen cruzando todas las explicaciones."""
        all_features = []

        for explanation in binary_explanations + classify_explanations:
            if "top_features" in explanation:
                all_features.extend(explanation["top_features"])

        if not all_features:
            return {"error": "No hay características para analizar"}

        feature_groups = {}
        for feature_data in all_features:
            feature_name = feature_data.get("feature", "unknown")
            if feature_name not in feature_groups:
                feature_groups[feature_name] = []
            feature_groups[feature_name].append(feature_data)

        feature_summary = []
        for feature_name, feature_list in feature_groups.items():
            avg_impact = np.mean([f.get("impact", 0) for f in feature_list])
            avg_shap = np.mean([f.get("shap_value", 0) for f in feature_list])

            first_feature = feature_list[0]

            feature_summary.append({
                "feature": feature_name,
                "electrode": first_feature.get("electrode", "unknown"),
                "metric": first_feature.get("metric", "unknown"),
                "average_impact": float(avg_impact),
                "average_shap_value": float(avg_shap),
                "actual_value": first_feature.get("actual_value", 0),
                "status": first_feature.get("status", "unknown"),
                "z_score": first_feature.get("z_score", 0),
                "appearances": len(feature_list)
            })

        feature_summary.sort(key=lambda x: x["average_impact"], reverse=True)

        electrode_analysis = self._analyze_by_electrodes(feature_summary)

        metric_analysis = self._analyze_by_metrics(feature_summary)

        return {
            "most_influential_features": feature_summary[:5],
            "electrode_analysis": electrode_analysis,
            "metric_analysis": metric_analysis,
            "total_features_analyzed": len(feature_summary),
            "summary_interpretation": self._generate_summary_interpretation(feature_summary)
        }

    def _analyze_by_electrodes(self, feature_summary: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza importancia por electrodos."""
        electrode_impacts = {}

        for feature in feature_summary:
            electrode = feature["electrode"]
            if electrode not in electrode_impacts:
                electrode_impacts[electrode] = []
            electrode_impacts[electrode].append(feature["average_impact"])

        electrode_analysis = {}
        for electrode, impacts in electrode_impacts.items():
            electrode_analysis[electrode] = {
                "average_impact": float(np.mean(impacts)),
                "max_impact": float(np.max(impacts)),
                "feature_count": len(impacts)
            }

        sorted_electrodes = sorted(electrode_analysis.items(),
                                   key=lambda x: x[1]["average_impact"], reverse=True)

        return {
            "most_important_electrode": sorted_electrodes[0][0] if sorted_electrodes else "unknown",
            "electrode_rankings": dict(sorted_electrodes)
        }

    def _analyze_by_metrics(self, feature_summary: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza importancia por tipos de métricas."""
        metric_impacts = {}

        for feature in feature_summary:
            metric = feature["metric"]
            if metric not in metric_impacts:
                metric_impacts[metric] = []
            metric_impacts[metric].append(feature["average_impact"])

        metric_analysis = {}
        for metric, impacts in metric_impacts.items():
            metric_analysis[metric] = {
                "average_impact": float(np.mean(impacts)),
                "max_impact": float(np.max(impacts)),
                "feature_count": len(impacts)
            }

        sorted_metrics = sorted(metric_analysis.items(),
                                key=lambda x: x[1]["average_impact"], reverse=True)

        return {
            "most_important_metric": sorted_metrics[0][0] if sorted_metrics else "unknown",
            "metric_rankings": dict(sorted_metrics)
        }

    def _generate_summary_interpretation(self, feature_summary: List[Dict[str, Any]]) -> str:
        """Genera interpretación textual del resumen."""
        if not feature_summary:
            return "No se encontraron patrones significativos."

        top_feature = feature_summary[0]
        interpretation = f"El factor más influyente es {top_feature['metric']} en {top_feature['electrode']} "
        interpretation += f"con un valor de {top_feature['actual_value']:.3f} ({top_feature['status']}). "

        abnormal_count = sum(1 for f in feature_summary[:5] if f['status'] != 'normal')
        if abnormal_count > 0:
            interpretation += f"Se detectaron {abnormal_count} características con valores anómalos "
            interpretation += "que contribuyen significativamente a la predicción."
        else:
            interpretation += "Las características principales están en rangos normales."

        return interpretation


ml_explainer = MLExplainer()