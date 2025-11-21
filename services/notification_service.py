# services/notification_service.py

from models.userModel import User, NotificationPreferenceEnum
from models.newsModel import News, TagEnum, StatusEnum
from enum import Enum as PyEnum
from models.notificationModel import Notification, UserNotification
from app import db
import threading
from flask import current_app
from services.email_service import send_email
from flask import url_for

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
            'VAGA': 'VAGA'
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
            if user.id == news.author_id:
                continue
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
            # Gerar link para a notícia
            news_link = url_for('news_routes.render_news_template', _external=True) + f'?id={news.id}'
            html_body = f'<p>Nova notícia: <a href="{news_link}">{news.title}</a> ({tag.value})</p>'
            recipients.append((user.email, message, html_body))

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
                for email, msg, html in recipients_list:
                    try:
                        send_email(email, 'Nova Notificação', msg, html=html)
                    except Exception:
                        app_ctx.logger.exception("Falha ao enviar e-mail para %s", email)

        thread = threading.Thread(target=_send_all_emails, args=(recipients, app), daemon=True)
        thread.start()

# Função para buscar últimas 10 notificações e contar não visualizadas

def get_user_notifications(user_id: int):
    notifications = UserNotification.query.filter_by(user_id=user_id).order_by(UserNotification.sent_at.desc()).limit(10).all()
    unread_count = UserNotification.query.filter_by(user_id=user_id, viewed=False).count()
    return notifications, unread_count

def notify_author_approval(news: News):
    if not news.author_id:
        return
    author = User.query.get(news.author_id)
    if not author:
        return
    author_msg = f'Sua notícia "{news.title}" foi aceita.'
    notif = Notification(news_id=news.id, message=author_msg)
    db.session.add(notif)
    db.session.flush()
    un = UserNotification(user_id=author.id, notification_id=notif.id)
    db.session.add(un)
    db.session.commit()
    # send email
    news_link = url_for('news_routes.render_news_template', _external=True) + f'?id={news.id}'
    html_body = f'<p>Sua notícia <a href="{news_link}">{news.title}</a> foi aceita.</p>'
    app = current_app._get_current_object()
    def _send_email():
        with app.app_context():
            try:
                send_email(author.email, 'Sua notícia foi aceita', author_msg, html=html_body)
            except Exception:
                app.logger.exception('Falha ao enviar e-mail de aceite para autor %s', author.email)
    threading.Thread(target=_send_email, daemon=True).start()

def notify_author_rejection(news: News):
    if not news.author_id:
        return
    author = User.query.get(news.author_id)
    if not author:
        return
    author_msg = f'Sua notícia "{news.title}" foi rejeitada.'
    notif = Notification(news_id=news.id, message=author_msg)
    db.session.add(notif)
    db.session.flush()
    un = UserNotification(user_id=author.id, notification_id=notif.id)
    db.session.add(un)
    db.session.commit()
    # send email
    news_link = url_for('news_routes.render_news_template', _external=True) + f'?id={news.id}'
    html_body = f'<p>Sua notícia <a href="{news_link}">{news.title}</a> foi rejeitada.</p>'
    app = current_app._get_current_object()
    def _send_email():
        with app.app_context():
            try:
                send_email(author.email, 'Sua notícia foi rejeitada', author_msg, html=html_body)
            except Exception:
                app.logger.exception('Falha ao enviar e-mail de rejeição para autor %s', author.email)
    threading.Thread(target=_send_email, daemon=True).start()

def notify_users_for_added_tags(news: News, added_tags):
    if not added_tags:
        return
    news_link = url_for('news_routes.render_news_template', _external=True) + f'?id={news.id}'
    from sqlalchemy.dialects.postgresql import array
    from sqlalchemy import cast
    for tag in added_tags:
        tag_value = tag.value
        users_to_notify = User.query.filter(
            User.notification_preferences.op('@>')(cast(array([tag_value]), User.notification_preferences.type)) | User.notification_preferences.op('@>')(cast(array(['TODOS']), User.notification_preferences.type))
        ).filter(
            ~User.id.in_(
                db.session.query(UserNotification.user_id).join(Notification).filter(Notification.news_id == news.id)
            )
        ).filter(User.id != news.author_id).all()
        for user in users_to_notify:
            try:
                msg = f'Nova notícia com tag {tag_value}: "{news.title}"'
                html_body = f'<p>Nova notícia com tag {tag_value}: <a href="{news_link}">{news.title}</a></p>'
                notif = Notification(news_id=news.id, message=msg)
                db.session.add(notif)
                db.session.flush()
                un = UserNotification(user_id=user.id, notification_id=notif.id)
                db.session.add(un)
                db.session.commit()
                app = current_app._get_current_object()
                def _send_email():
                    with app.app_context():
                        try:
                            send_email(user.email, f'Notificação: {tag_value}', msg, html=html_body)
                        except Exception:
                            app.logger.exception('Falha ao enviar e-mail para %s', user.email)
                threading.Thread(target=_send_email, daemon=True).start()
            except Exception:
                current_app.logger.exception('Erro ao notificar usuário %s para tag %s', user.id, tag_value)
