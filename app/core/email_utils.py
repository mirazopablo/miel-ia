import os
from pathlib import Path
from datetime import datetime
from loguru import logger as log
from app.core.config import settings

def send_reset_email(to_email: str, token: str):
    """
    Simula el envío de un email de recuperación de contraseña.
    Dependiendo de la configuración, guarda el email como archivo o lo imprime en consola.
    """
    if not settings.EMAILS_ENABLED:
        log.warning("Emails are disabled in configuration.")
        return

    subject = "Recuperación de Contraseña - Miel-IA"
    reset_link = f"http://localhost:3000/reset-password?token={token}"
    
    html_content = f"""
    <html>
        <body>
            <h1>Recuperación de Contraseña</h1>
            <p>Hola,</p>
            <p>Has solicitado restablecer tu contraseña en Miel-IA.</p>
            <p>Haz clic en el siguiente enlace para continuar:</p>
            <a href="{reset_link}">Restablecer Contraseña</a>
            <p>Si no has solicitado esto, puedes ignorar este correo.</p>
            <p><small>Este enlace expirará en {settings.RESET_TOKEN_EXPIRE_MINUTES} minutos.</small></p>
        </body>
    </html>
    """
    
    if settings.EMAIL_BACKEND == "file":
        _save_email_to_file(to_email, subject, html_content)
    elif settings.EMAIL_BACKEND == "console":
        _print_email_to_console(to_email, subject, reset_link)
    else:
        log.warning(f"Unknown email backend: {settings.EMAIL_BACKEND}")

def _save_email_to_file(to_email: str, subject: str, content: str):
    """Guarda el email como un archivo HTML en app/emails_out/"""
    try:
        # Crear directorio si no existe
        base_dir = Path(__file__).resolve().parent.parent.parent
        emails_dir = base_dir / "app" / "emails_out"
        emails_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"email_{to_email}_{timestamp}.html"
        file_path = emails_dir / filename
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"<!-- To: {to_email} -->\n")
            f.write(f"<!-- Subject: {subject} -->\n")
            f.write(content)
            
        log.info(f"Email saved to {file_path}")
        
    except Exception as e:
        log.error(f"Error saving email to file: {e}")

def _print_email_to_console(to_email: str, subject: str, link: str):
    """Imprime el link de recuperación en la consola"""
    print("\n" + "="*50)
    print(f"📧 EMAIL SIMULADO PARA: {to_email}")
    print(f"ASUNTO: {subject}")
    print(f"LINK: {link}")
    print("="*50 + "\n")
