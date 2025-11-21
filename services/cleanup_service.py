# services/cleanup_service.py

from flask import current_app
from models.newsModel import News, StatusEnum
from models.notificationModel import Notification
from app import db
from datetime import datetime, timedelta, timezone
import os

def cleanup_rejected_news():
    with current_app.app_context():
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        rejected_news = News.query.filter(News.status == StatusEnum.REJEITADA, News.created_at < cutoff).all()
        count = len(rejected_news)
        for n in rejected_news:
            # delete image
            if n.image:
                relative_path = n.image.replace('/static/', '', 1)
                img_path = os.path.join(current_app.static_folder, relative_path)
                if os.path.exists(img_path):
                    try:
                        os.remove(img_path)
                        current_app.logger.info(f'Imagem deletada para notícia rejeitada: {img_path}')
                    except Exception as e:
                        current_app.logger.warning(f'Falha ao deletar imagem da notícia rejeitada {img_path}: {e}')
            # delete notifications
            Notification.query.filter_by(news_id=n.id).delete()
            db.session.delete(n)
        db.session.commit()
        current_app.logger.info(f'Limpeza concluída: {count} notícias rejeitadas deletadas.')
        return count