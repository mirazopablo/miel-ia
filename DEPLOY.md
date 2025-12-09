# 🚀 Guía de Despliegue para Miel-IA

Esta guía describe cómo desplegar y gestionar el backend de Miel-IA en tu servidor (VM de la universidad) utilizando **Docker Compose**.

Esta es la forma recomendada de correr la aplicación en un servidor, ya que asegura que:
- La aplicación se reinicie automáticamente si falla o si se reinicia el servidor.
- Los logs se gestionen correctamente.
- El entorno sea consistente (mismas versiones de Python, librerías, etc.).

---

## 📋 Prerrequisitos

Asegúrate de tener instalados:
1.  **Docker**
2.  **Git**

Puedes verificarlo corriendo:
```bash
docker compose version
git --version
```

---

## 🛠️ Instalación Inicial

1.  **Clonar el repositorio** (si aún no lo has hecho):
    ```bash
    git clone https://github.com/mirazopablo/miel-ia.git
    cd miel-ia
    ```

2.  **Configurar variables de entorno**:
    Crea un archivo `.env` basado en el ejemplo:
    ```bash
    cp .env-example .env
    ```
    Edita el archivo `.env` con tus configuraciones (credenciales de base de datos, etc.) si es necesario.

---

## 🏃‍♂️ Ejecutar la Aplicación

Para iniciar la aplicación en segundo plano (modo "detached"):

```bash
docker compose up -d --build
```

- `-d`: Corre los contenedores en el fondo (background).
- `--build`: Fuerza la reconstrucción de la imagen (útil si cambiaste código).

La API estará disponible en: `http://localhost:8000` (o la IP de tu VM).

---

## 🔄 Actualizar la Aplicación

Cuando hagas cambios en tu código y los subas a GitHub, sigue estos pasos para actualizar el servidor:

1.  **Descargar los últimos cambios**:
    ```bash
    git pull origin main
    ```

2.  **Reiniciar los contenedores con el nuevo código**:
    ```bash
    docker compose up -d --build
    ```
    Docker detectará los cambios, reconstruirá la imagen y reiniciará el servicio con la nueva versión.

---

## 🔍 Ver Logs y Estado

- **Ver si los contenedores están corriendo**:
    ```bash
    docker compose ps
    ```

- **Ver los logs de la aplicación** (para depurar errores):
    ```bash
    docker compose logs -f
    ```
    (Presiona `Ctrl+C` para salir de los logs).

- **Detener la aplicación**:
    ```bash
    docker compose down
    ```

---

## ❓ Preguntas Frecuentes

**¿Por qué no usar `uvicorn` directamente?**
Correr `uvicorn` manualmente (`uvicorn main:app ...`) está bien para desarrollo local, pero en un servidor, si cierras la terminal, se cierra el proceso. Docker se encarga de mantenerlo vivo siempre.

**¿Cómo reinicio si algo falla?**
Simplemente corre `docker compose restart`.
