# services/email_service.py

from flask_mail import Message
from app import mail

def send_email(to, subject, body, html=None):
    msg = Message(subject, recipients=[to], body=body)
    if html:
        msg.html = html
    mail.send(msg)
