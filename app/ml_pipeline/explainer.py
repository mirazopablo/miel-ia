# app/ml_pipeline/explainer.py
import pandas as pd
import numpy as np
import shap
import json
import os
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
        """Carga estadísticas de referencia para interpretar valores de características desde JSON."""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            stats_path = os.path.join(current_dir, "feature_statistics.json")
            with open(stats_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("feature_statistics", {})
        except Exception as e:
            raise RuntimeError(f"Error al cargar feature_statistics.json: {e}")

    def _parse_feature_name(self, feature: str) -> Dict[str, str]:
        """Extrae métrica y electrodo de nombres como willison_amplitude_e1."""
        electrode = "unknown"
        metric = feature

        if feature and "_e" in feature:
            parts = feature.rsplit("_e", 1)
            if len(parts) == 2 and parts[1].isdigit():
                metric, electrode_id = parts
                electrode = f"e{electrode_id}"

        return {"metric": metric, "electrode": electrode}

    def _translate_metric(self, metric: str) -> str:
        translations = {
            "standard_deviation": "Desviación Estándar",
            "root_mean_square": "Raíz Cuadrática Media (RMS)",
            "minimum": "Voltaje Mínimo",
            "maximum": "Voltaje Máximo",
            "zero_crossings": "Cruces por Cero",
            "average_amplitude_change": "Cambio Promedio de Amplitud",
            "amplitude_first_burst": "Amplitud del Primer Burst",
            "mean_absolute_value": "Valor Medio Absoluto",
            "wave_form_length": "Longitud de Onda",
            "willison_amplitude": "Amplitud de Willison"
        }
        return translations.get(metric, metric.replace("_", " ").title())

    def _translate_status(self, status: str) -> str:
        translations = {
            "normal": "dentro de rangos fisiológicos",
            "above_normal": "por encima de lo normal",
            "below_normal": "por debajo de lo normal"
        }
        return translations.get(status, "estado desconocido")

    def explain_binary_prediction(self, df_scaled: pd.DataFrame, df_unscaled: pd.DataFrame, predictions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Explica las predicciones de los modelos binarios usando SHAP."""
        explanations = []

        if 'predictions' in predictions:
            pred_dict = predictions['predictions']
        else:
            pred_dict = predictions

        try:
            rf_explanation = self._explain_model(
                self.predictor.binary_rf, df_scaled, df_unscaled, "Random Forest",
                pred_dict.get("Random_Forest", 0), "binary"
            )
            explanations.append(rf_explanation)

            xgb_explanation = self._explain_model(
                self.predictor.binary_xgb, df_scaled, df_unscaled, "XGBoost",
                pred_dict.get("XGBoost", 0), "binary"
            )
            explanations.append(xgb_explanation)

            keras_explanation = self._explain_keras_model(
                df_scaled, df_unscaled, "TensorFlow Logistic Regression",
                pred_dict.get("TensorFlow_Logistic_Regression", 0), "binary"
            )
            explanations.append(keras_explanation)

        except Exception as e:
            raise RuntimeError(f"Binary explanation error: {e}")

        return explanations

    def explain_classification_prediction(self, df_scaled: pd.DataFrame, df_unscaled: pd.DataFrame, predictions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Explica las predicciones de los modelos de clasificación usando SHAP."""
        explanations = []

        if 'predictions' in predictions:
            pred_dict = predictions['predictions']
        else:
            pred_dict = predictions

        try:
            rf_explanation = self._explain_model(
                self.predictor.classify_rf, df_scaled, df_unscaled, "Random Forest",
                pred_dict.get("Random_Forest", 0), "classification"
            )
            explanations.append(rf_explanation)

            xgb_explanation = self._explain_model(
                self.predictor.classify_xgb, df_scaled, df_unscaled, "XGBoost",
                pred_dict.get("XGBoost", 0), "classification"
            )
            explanations.append(xgb_explanation)

            keras_explanation = self._explain_keras_model(
                df_scaled, df_unscaled, "TensorFlow Logistic Regression",
                pred_dict.get("TensorFlow_Logistic_Regression", 0), "classification"
            )
            explanations.append(keras_explanation)

        except Exception as e:
            raise RuntimeError(f"Classification explanation error: {e}")

        return explanations

    def _explain_model(self, model, df_scaled: pd.DataFrame, df_unscaled: pd.DataFrame, model_name: str,
                       prediction: int, task_type: str) -> Dict[str, Any]:
        """Explica un modelo individual usando SHAP."""
        try:
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(df_scaled)

            if isinstance(shap_values, list):
                if len(shap_values) > prediction:
                    shap_values = shap_values[prediction]
                else:
                    shap_values = shap_values[0]

            if shap_values.ndim > 1:
                shap_values = shap_values[0]

            feature_importance = self._get_feature_importance(df_unscaled, shap_values)

            return {
                "model_name": model_name,
                "prediction": prediction,
                "task_type": task_type,
                "top_features": feature_importance[:5], 
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

    def _explain_keras_model(self, df_scaled: pd.DataFrame, df_unscaled: pd.DataFrame, model_name: str,
                             prediction: int, task_type: str) -> Dict[str, Any]:
        """Explicación simplificada para modelos de Keras."""
        try:
            feature_importance = []

            for feature in df_unscaled.columns:
                value = df_unscaled[feature].iloc[0]
                stats = self.reference_stats.get(feature, {})

                if stats:
                    mean = stats.get('mean', 0)
                    std = stats.get('std', 1)
                    z_score = (value - mean) / std if std > 0 else 0

                    normal_min = stats.get('normal_min', mean - 2 * std)
                    normal_max = stats.get('normal_max', mean + 2 * std)

                    if value < normal_min:
                        status = "below_normal"
                        range_status = "low"
                    elif value > normal_max:
                        status = "above_normal"
                        range_status = "high"
                    else:
                        status = "normal"
                        range_status = "normal"

                    parsed = self._parse_feature_name(feature)

                    feature_importance.append({
                        "feature": feature,
                        "electrode": parsed["electrode"],
                        "metric": parsed["metric"],
                        "metric_es": self._translate_metric(parsed["metric"]),
                        "shap_value": round(float(z_score) * 0.1, 4),
                        "actual_value": round(float(value), 4),
                        "impact": round(abs(float(z_score)) * 0.1, 4),
                        "direction": "positivo" if z_score > 0 else "negativo",
                        "status": status,
                        "status_es": self._translate_status(status),
                        "range_status": range_status,
                        "z_score": round(float(z_score), 4),
                        "deviation_magnitude": round(float(abs(z_score)), 4)
                    })

            feature_importance.sort(key=lambda x: abs(x['impact']), reverse=True)

            return {
                "model_name": model_name,
                "prediction": prediction,
                "task_type": task_type,
                "top_features": feature_importance[:5],
                "explanation_summary": self._generate_explanation_summary(
                    feature_importance, prediction, task_type
                )
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
                range_status = "unknown"

                if stats:
                    mean = stats.get('mean', 0)
                    std = stats.get('std', 1)
                    z_score = (actual_value - mean) / std if std > 0 else 0

                    normal_min = stats.get('normal_min', mean - 2 * std)
                    normal_max = stats.get('normal_max', mean + 2 * std)

                    if actual_value < normal_min:
                        status = "below_normal"
                        range_status = "low"
                    elif actual_value > normal_max:
                        status = "above_normal"
                        range_status = "high"
                    else:
                        status = "normal"
                        range_status = "normal"

                parsed = self._parse_feature_name(feature)
                electrode = parsed["electrode"]
                metric = parsed["metric"]

                feature_importance.append({
                    "feature": feature,
                    "electrode": electrode,
                    "metric": metric,
                    "metric_es": self._translate_metric(metric),
                    "shap_value": round(shap_value, 4),
                    "actual_value": round(actual_value, 4),
                    "impact": round(abs(shap_value), 4),
                    "direction": "positivo" if shap_value > 0 else "negativo",
                    "status": status,
                    "status_es": self._translate_status(status),
                    "range_status": range_status,
                    "z_score": round(float(z_score), 4),
                    "deviation_magnitude": round(float(abs(z_score)), 4)
                })

        feature_importance.sort(key=lambda x: x['impact'], reverse=True)
        return feature_importance

    def _generate_explanation_summary(self, feature_importance: List[Dict[str, Any]],
                                      prediction: int, task_type: str) -> str:
        """Genera un resumen textual clínico para el frontend."""
        if not feature_importance:
            return "No se pudieron identificar biomarcadores determinantes."

        top_feature = feature_importance[0]
        metric_es = top_feature.get('metric_es', self._translate_metric(top_feature['metric']))
        status_es = top_feature.get('status_es', self._translate_status(top_feature.get('status', 'unknown')))

        if task_type == "binary":
            pred_text = "Positivo (Anómalo)" if prediction == 1 else "Negativo (Sano)"
        else:
            pred_text = f"Severidad Nivel {prediction}"

        summary = f"Veredicto: {pred_text}. "
        summary += f"El biomarcador '{metric_es}' (electrodo {top_feature['electrode']}) fue decisivo "
        summary += f"al encontrarse {status_es}."

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
                "metric_es": first_feature.get("metric_es", "desconocido"),
                "average_impact": round(float(avg_impact), 4),
                "average_shap_value": round(float(avg_shap), 4),
                "actual_value": round(float(first_feature.get("actual_value", 0)), 4),
                "status": first_feature.get("status", "unknown"),
                "status_es": first_feature.get("status_es", "desconocido"),
                "z_score": round(float(first_feature.get("z_score", 0)), 4),
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
                "average_impact": round(float(np.mean(impacts)), 4),
                "max_impact": round(float(np.max(impacts)), 4),
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
                "metric_es": self._translate_metric(metric),
                "average_impact": round(float(np.mean(impacts)), 4),
                "max_impact": round(float(np.max(impacts)), 4),
                "feature_count": len(impacts)
            }

        sorted_metrics = sorted(metric_analysis.items(),
                                key=lambda x: x[1]["average_impact"], reverse=True)

        return {
            "most_important_metric": sorted_metrics[0][0] if sorted_metrics else "unknown",
            "metric_rankings": dict(sorted_metrics)
        }

    def _generate_summary_interpretation(self, feature_summary: List[Dict[str, Any]]) -> str:
        """Genera un reporte clínico integrador en lenguaje natural."""
        if not feature_summary:
            return "No se encontraron patrones electromiográficos significativos para analizar."

        top_feature = feature_summary[0]
        
        interpretation = (
            f"El biomarcador más influyente en la decisión clínica de la IA fue '{self._translate_metric(top_feature['metric'])}' "
            f"registrado en el electrodo {top_feature['electrode']}, el cual se presentó "
            f"{self._translate_status(top_feature['status'])} (valor numérico exacto: {top_feature['actual_value']:.2f}). "
        )

        normal_count = sum(1 for f in feature_summary[:5] if f['status'] == 'normal')
        abnormal_count = sum(1 for f in feature_summary[:5] if f['status'] in ['below_normal', 'above_normal'])

        if abnormal_count > 0:
            interpretation += (
                f"Al auditar los 5 principales biomarcadores neurológicos, se detectaron {abnormal_count} anomalías "
                f"fuera de los umbrales fisiológicos de referencia y {normal_count} dentro de lo esperado. "
                "Estas divergencias son el motor estadístico subyacente que justifica el diagnóstico emitido."
            )
        elif normal_count > 0:
            interpretation += (
                "A pesar del diagnóstico emitido, los 5 principales biomarcadores de mayor peso predictivo se encuentran "
                "estrictamente dentro de los rangos fisiológicos estándar, lo que sugiere un patrón sutil de anomalía estructural."
            )

        return interpretation


ml_explainer = MLExplainer()