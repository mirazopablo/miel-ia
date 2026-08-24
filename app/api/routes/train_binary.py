from fastapi import APIRouter, BackgroundTasks, Depends
import subprocess
import os

from app.infrastructure.db.DTOs.auth_schema import UserOut
from ...api.v1.auth import get_current_user


train_binary= APIRouter()

@train_binary.post("/train-binary")
def train_models(background_tasks: BackgroundTasks, current_user: UserOut = Depends(get_current_user)):
    train_script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "scripts", "train_binary_pipeline.py"))

    trained_models_dir = os.path.abspath("trained_models/binary")

    os.makedirs(trained_models_dir, exist_ok=True)

    command = ["python", "-u", train_script_path]

    def run_training():
        try:
            print("Iniciando entrenamiento binario en segundo plano... Revisa la consola para ver el progreso detallado.")
            subprocess.run(command, check=True)
            print("Entrenamiento binario completado exitosamente.")
        except subprocess.CalledProcessError as e:
            print(f"Error durante el entrenamiento binario (Código de salida: {e.returncode})")

    background_tasks.add_task(run_training)

    return {"message": "Entrenamiento de modelos iniciado en segundo plano."}
