# alerting.py
from config import SMTP
from database import insert_event
import smtplib
from email.message import EmailMessage
import traceback

def alert_console(source, severity, message):
    print(f"[ALERT] {severity} | {source} | {message}")
    insert_event(source, severity, message)

def alert_email(subject, body):
    if not SMTP.get("enabled", False):
        return
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = SMTP["from_addr"]
        msg["To"] = ", ".join(SMTP["to_addrs"])
        msg.set_content(body)
        with smtplib.SMTP(SMTP["server"], SMTP["port"]) as s:
            s.starttls()
            s.login(SMTP["username"], SMTP["password"])
            s.send_message(msg)
    except Exception:
        traceback.print_exc()
