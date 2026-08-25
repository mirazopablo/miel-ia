import os
import tensorflow as tf
from loguru import logger as log

def convert_keras_to_tflite(model_path: str, output_path: str):
    """
    Convierte un archivo .keras a .tflite.
    """
    if not os.path.exists(model_path):
        log.error(f"Archivo no encontrado: {model_path}")
        return

    log.info(f"Cargando modelo Keras desde {model_path}...")
    try:
        model = tf.keras.models.load_model(model_path)
    except Exception as e:
        log.error(f"Error cargando modelo: {e}")
        return

    log.info("Convirtiendo a TFLite...")
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    
    tflite_model = converter.convert()

    with open(output_path, 'wb') as f:
        f.write(tflite_model)
    
    log.info(f"Modelo TFLite guardado exitosamente en: {output_path}")

def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "trained_models", "v2.0"))
    
    binary_model_path = os.path.join(base_dir, "binary", "models", "logistic_regression_model.keras")
    binary_output_path = os.path.join(base_dir, "binary", "models", "logistic_regression_model.tflite")
    
    classify_model_path = os.path.join(base_dir, "classify", "models", "logistic_regression_model.keras")
    classify_output_path = os.path.join(base_dir, "classify", "models", "logistic_regression_model.tflite")

    log.info("Iniciando conversión de modelos Binarios...")
    convert_keras_to_tflite(binary_model_path, binary_output_path)

    log.info("Iniciando conversión de modelos de Clasificación...")
    convert_keras_to_tflite(classify_model_path, classify_output_path)

if __name__ == "__main__":
    main()
