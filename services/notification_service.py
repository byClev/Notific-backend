# services/notification_service.py

from models.userModel import User, NotificationPreferenceEnum
from models.newsModel import News, TagEnum
from enum import Enum as PyEnum
from models.notificationModel import Notification, UserNotification
from app import db
import threading
from flask import current_app
from services.email_service import send_email

def notify_users_for_news(news: News):
    if not news.tags:
        return

    recipients = []  # lista de tuplas (email, message)

    for tag in news.tags:
        try:
            tag_key = tag.name if isinstance(tag, PyEnum) else str(tag).upper()
        except Exception:
            tag_key = str(tag).upper()

        mapping = {
            'PROJETO': 'PROJETO',
            'EVENTO': 'EVENTO',
            'VAGA': 'OPORTUNIDADE'
        }

        pref_name = mapping.get(tag_key)
        if not pref_name:
            continue

        try:
            pref_enum = NotificationPreferenceEnum[pref_name]
        except Exception:
            continue

        users = User.query.filter(User.notification_preferences.any(pref_enum)).all()
        for user in users:
            # Verifica se já existe notificação para esse usuário e notícia
            exists = UserNotification.query.join(Notification).filter(
                UserNotification.user_id == user.id,
                Notification.news_id == news.id
            ).first()
            if exists:
                continue  # já notificou esse usuário para essa notícia

            message = f'Nova notícia: {news.title} ({tag.value})'
            notification = Notification(news_id=news.id, message=message)
            db.session.add(notification)
            db.session.flush()
            user_notification = UserNotification(user_id=user.id, notification_id=notification.id)
            db.session.add(user_notification)
            recipients.append((user.email, message))

    # commit das notificações e relacionamentos primeiro
    if recipients:
        db.session.commit()
    else:
        # se não houve destinatários apenas rollback/commit para garantir consistência
        db.session.commit()

    # envio assíncrono dos e-mails em uma thread separada
    if recipients:
        app = current_app._get_current_object()

        def _send_all_emails(recipients_list, app_ctx):
            with app_ctx.app_context():
                for email, msg in recipients_list:
                    try:
                        send_email(email, 'Nova Notificação', msg)
                    except Exception:
                        app_ctx.logger.exception("Falha ao enviar e-mail para %s", email)

        thread = threading.Thread(target=_send_all_emails, args=(recipients, app), daemon=True)
        thread.start()

# Função para buscar últimas 10 notificações e contar não visualizadas

def get_user_notifications(user_id: int):
    notifications = UserNotification.query.filter_by(user_id=user_id).order_by(UserNotification.sent_at.desc()).limit(10).all()
    unread_count = UserNotification.query.filter_by(user_id=user_id, viewed=False).count()
    return notifications, unread_count
