import smtplib
from email.message import EmailMessage
from .config import settings

SUBJECT_PREFIX = "Polymarket异常警报"

def send_alert_email(wallet, amount_usdc, market_name, trigger_reason):
    if not settings.SMTP_HOST or not settings.ALERT_RECIPIENT:
        print("SMTP or recipient not configured; skipping email")
        return

    msg = EmailMessage()
    msg["From"] = settings.SMTP_USER
    msg["To"] = settings.ALERT_RECIPIENT
    msg["Subject"] = f"{SUBJECT_PREFIX} — {trigger_reason}"

    body = f"钱包: {wallet}\n金额(USDC): {amount_usdc}\n市场: {market_name}\n触发原因: {trigger_reason}\n"
    msg.set_content(body)

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as s:
        s.starttls()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        s.send_message(msg)
        print(f"Alert sent for {wallet} — {trigger_reason}")
