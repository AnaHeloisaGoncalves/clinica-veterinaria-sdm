import logging
import os
import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import urlencode

from fastapi import HTTPException

logger = logging.getLogger("uvicorn.error")


def enviar_acesso(email, codigo, finalidade):
    base = os.getenv("CLINICA_PUBLIC_URL", "http://127.0.0.1:8000").rstrip("/")
    link = base + "/#" + urlencode({"acao": finalidade, "codigo": codigo})
    host = os.getenv("CLINICA_SMTP_HOST")
    if not host:
        logger.info("E-mail simulado para %s (%s): %s", email, finalidade, link)
        return

    mensagem = EmailMessage()
    mensagem["From"] = os.getenv("CLINICA_SMTP_FROM", "")
    mensagem["To"] = email
    mensagem["Subject"] = "Convite para a clínica" if finalidade == "convite" else "Redefinição de senha da clínica"
    mensagem.set_content(f"Abra o link abaixo para definir sua senha. Ele vale por uma hora e pode ser usado uma vez.\n\n{link}")
    try:
        with smtplib.SMTP(host, int(os.getenv("CLINICA_SMTP_PORT", "587")), timeout=8) as smtp:
            smtp.starttls(context=ssl.create_default_context())
            usuario = os.getenv("CLINICA_SMTP_USER")
            if usuario:
                smtp.login(usuario, os.getenv("CLINICA_SMTP_PASSWORD", ""))
            smtp.send_message(mensagem)
    except (OSError, ValueError):
        logger.error("Falha no envio de e-mail de acesso (%s).", finalidade)
        raise HTTPException(503, "O e-mail não pôde ser enviado. Tente novamente.") from None


def enviar_recuperacao(email, codigo):
    try:
        enviar_acesso(email, codigo, "recuperacao")
    except HTTPException:
        pass  # A resposta pública de recuperação é igual para todos os endereços.
