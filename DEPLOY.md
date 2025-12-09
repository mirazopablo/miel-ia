# 🚀 Guía Definitiva de Despliegue: Miel-IA

Esta documentación está actualizada para la arquitectura de despliegue en **infraestructura privada (VM de Universidad / OpenStack)** utilizando **GitHub Self-Hosted Runners**.

---

## 🏗️ Arquitectura de Despliegue

El despliegue ya no depende de conexiones SSH externas desde GitHub Cloud, lo cual elimina problemas de Firewall, VPNs y direcciones IP Privadas.

-   **Runner**: Agente de GitHub instalado en el propio servidor (`runs-on: self-hosted`).
-   **Red**: El deploy ocurre `localhost` -> `localhost`. No sale a internet.
-   **Trigger**: Push a la rama `main`.
-   **Ruta de Instalación**: `/home/ubuntu/miel-ia`.

---

## 🤖 Pipeline de CI/CD (Automático)

Cada vez que haces un `push` a `main`, se activa el workflow `.github/workflows/deploy.yml`.

### Pasos del Pipeline:

1.  **Check de Dependencias (MySQL)**:
    -   Verifica si el contenedor de MySQL está corriendo.
    -   Si no lo está, intenta iniciarlo navegando a `/home/ubuntu/mysql`.

2.  **Inicialización del Proyecto**:
    -   Define la ruta base: `/home/ubuntu/miel-ia`.
    -   **Auto-Healing**:
        -   Si la carpeta no existe, la crea.
        -   Si la carpeta está vacía (sin `.git`), ejecuta `git clone` automáticamente.
        -   Si ya existe, ejecuta `git pull` para bajar cambios.

3.  **Despliegue con Docker Compose**:
    -   Ejecuta `docker compose up -d --build --remove-orphans`.
    -   Esto reconstruye las imágenes si el `Dockerfile` cambió y levanta los servicios.

---

## 🔐 Secretos Requeridos

Aunque el runner es local, el script utiliza algunos secretos para configurar el entorno SSH (aunque ahora es redundante, se mantiene por compatibilidad con ssh-action) o para futuras expansiones.

| Secreto          | Descripción                                     |
| ---------------- | ----------------------------------------------- |
| `SSH_HOST`       | IP Privada de la VM (`10.201.1.236`)            |
| `SSH_USERNAME`   | Usuario del servidor (`ubuntu`)                 |
| `SSH_KEY`        | Llave Privada SSH (para conectar `ssh-action`)  |
| `SSH_PASSPHRASE` | Contraseña de la llave (si aplica)              |
| `PROJECT_PATH`   | **(Deprecado)** *Ahora hardcodeado en script*   |

---

## 🛠️ Gestión Manual (En caso de emergencia)

Si GitHub se cae o el runner falla, siempre puedes desplegar manualmente conectándote por SSH/VPN:

```bash
cd /home/ubuntu/miel-ia
git pull origin main
docker compose up -d --build
```

### Comandos Útiles

-   **Ver estado de contenedores**: `docker compose ps`
-   **Ver logs en vivo**: `docker compose logs -f`
-   **Reiniciar servicio**: `docker compose restart app`

---

## 🐛 Solución de Problemas Comunes

### 1. "Process exited with status 1" (Git Error)
Si ves errores como `not a git repository`, significa que la carpeta se corrompió.
**Solución**: Borra la carpeta y deja que el script la clone de nuevo.
```bash
rm -rf /home/ubuntu/miel-ia
# Vuelve a ejecutar el workflow en GitHub
```

### 2. "Runner is offline"
Si el deploy no inicia nunca.
**Solución**: Verifica el servicio en el servidor.
```bash
sudo ./svc.sh status
# Si está detenido:
sudo ./svc.sh start
```

### 3. "MySQL connection refused"
La app no conecta a la base de datos.
**Solución**: Verifica que la red externa de MySQL esté activa.
```bash
docker network ls
# Debe existir una red llamada 'mysql_network' o similar.
```
