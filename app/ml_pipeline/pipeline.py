import pandas as pd
from typing import IO
from .predictor import ml_predictor
from .helpers import validate_data, should_classify, build_final_verdict, generate_human_readable_summary
from .explainer import ml_explainer


def run_diagnosis_pipeline(file_stream: IO, include_explanations: bool = True) -> dict:
    """
    Ejecuta el pipeline completo de diagnóstico desde un stream de archivo.
    Ahora incluye explicabilidad usando SHAP.

    Args:
        file_stream: Un objeto tipo archivo (como el de UploadFile.file de FastAPI).
        include_explanations: Si incluir explicaciones SHAP (por defecto True)

    Returns:
        Un diccionario con el veredicto final, detalles del proceso y explicabilidad.
    """
    try:
        df = pd.read_csv(file_stream)
        df_valid = validate_data(df)
    except Exception as e:
        raise ValueError(f"Error processing CSV file: {e}")

    # Preparar datos (escalado automático + detección de normalización)
    df_binary_scaled, df_unscaled = ml_predictor.prepare_data(df_valid, "binary")

    binary_predictions = ml_predictor.predict_binary(df_binary_scaled)

    classify_predictions = None
    df_classify_scaled = None
    if should_classify(binary_predictions):
        df_classify_scaled, _ = ml_predictor.prepare_data(df_valid, "classify")
        classify_predictions = ml_predictor.predict_classify(df_classify_scaled)
    else:
        pass
    binary_explanations = None
    classify_explanations = None
    summary_insights = None

    if include_explanations:
        try:
            print("🔍 Generando explicaciones SHAP...")

            binary_explanations = ml_explainer.explain_binary_prediction(df_binary_scaled, df_unscaled, binary_predictions)

            if classify_predictions:
                classify_explanations = ml_explainer.explain_classification_prediction(df_classify_scaled, df_unscaled, classify_predictions)

            summary_insights = ml_explainer.generate_summary_insights(
                binary_explanations or [],
                classify_explanations or []
            )

        except Exception as e:
            raise RuntimeError(f"Error generating explanations: {e}")
            binary_explanations = None
            classify_explanations = None
            summary_insights = None

    final_verdict = build_final_verdict(
        binary_predictions,
        classify_predictions,
        binary_explanations,
        classify_explanations,
        summary_insights
    )

    readable_summary = generate_human_readable_summary(final_verdict)

    return final_verdict