import os
import smtplib
from email.message import EmailMessage
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
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Recuperación de Contraseña - Miel-IA</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol";
                line-height: 1.6;
                color: #333;
                background-color: hsl(0 0% 100%); /* Color de fondo */
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 20px auto;
                background-color: #ffffff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                background-color: hsl(221.2 83.2% 53.3%); /* Color primary */
                padding: 20px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                text-align: center;
            }}
            .header img {{
                max-width: 100%;
                height: auto;
                border-radius: 4px;
            }}
            .content {{
                padding: 20px;
                text-align: left;
            }}
            .button-container {{
                text-align: center;
                margin: 20px 0;
            }}
            .button {{
                display: inline-block;
                background-color: hsl(221.2 83.2% 53.3%); /* Color primary */
                color: #ffffff;
                padding: 10px 20px;
                border-radius: 5px;
                text-decoration: none;
                font-weight: bold;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                font-size: 0.8em;
                color: #777;
            }}
            .expiration-note {{
                color: hsl(0 84.2% 60.2%); /* Color destructive */
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <img src="{settings.EMAIL_BANNER_URL}" alt="Miel-IA Banner">
            </div>
            <div class="content">
                <h1>Recuperación de Contraseña</h1>
                <p>Hola,</p>
                <p>Has solicitado restablecer tu contraseña en <strong>Miel-IA</strong>.</p>
                <p>Haz clic en el siguiente botón para continuar:</p>
                <div class="button-container">
                    <a href="{reset_link}" class="button">Restablecer Contraseña</a>
                </div>
                <p>Si no has solicitado esto, puedes ignorar este correo.</p>
                <p class="expiration-note">Este enlace expirará en {settings.RESET_TOKEN_EXPIRE_MINUTES} minutos.</p>
            </div>
            <div class="footer">
                <p>&copy; {datetime.now().year} Miel-IA. Todos los derechos reservados.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    if settings.EMAIL_BACKEND == "file":
        _save_email_to_file(to_email, subject, html_content)
    elif settings.EMAIL_BACKEND == "console":
        _print_email_to_console(to_email, subject, reset_link)
    elif settings.EMAIL_BACKEND == "smtp":
        _send_email_smtp(to_email, subject, html_content)
    else:
        log.warning(f"Unknown email backend: {settings.EMAIL_BACKEND}")


def _send_email_smtp(to_email: str, subject: str, html_content: str):
    """Envía el email mediante SMTP (Gmail/relay propio/etc.)."""
    if not settings.SMTP_HOST or not settings.SMTP_PORT or not settings.SMTP_FROM:
        log.error("SMTP configuration missing: SMTP_HOST, SMTP_PORT o SMTP_FROM no están configurados")
        return

    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to_email
        msg.set_content("Este correo está en HTML. Si lo ves en un cliente de texto, copia y pega el link")
        msg.add_alternative(html_content, subtype="html")

        if settings.SMTP_SSL:
            smtp = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20)
        else:
            smtp = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20)

        try:
            if settings.SMTP_TLS and not settings.SMTP_SSL:
                smtp.ehlo()
                smtp.starttls()
                smtp.ehlo()

            if settings.SMTP_USER and settings.SMTP_PASS:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASS)

            smtp.send_message(msg)
            log.info(f"Email enviado vía SMTP a {to_email}")

        finally:
            smtp.quit()

    except Exception as e:
        log.error(f"Error enviando email vía SMTP: {e}")

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
