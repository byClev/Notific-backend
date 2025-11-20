# routes/notification.py

from flask import Blueprint, request, jsonify
from app import db
from models.notificationModel import UserNotification, Notification
from models.newsModel import News
from routes.decorators import token_required

notification_routes = Blueprint('notification_routes', __name__)

@notification_routes.route('/notifications/unread-count', methods=['GET'])
@token_required
def unread_count():
    user = getattr(request, 'user', None)
    if not user:
        return jsonify({'success': False, 'error': 'Usuário não autenticado'}), 401
    count = UserNotification.query.filter_by(user_id=user.id, viewed=False).count()
    return jsonify({'success': True, 'count': count})

@notification_routes.route('/notifications', methods=['GET'])
@token_required
def get_notifications():
    user = getattr(request, 'user', None)
    if not user:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    # Paginação
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    query = db.session.query(UserNotification).join(Notification).join(News).filter(UserNotification.user_id == user.id).order_by(UserNotification.viewed.asc(), News.updated_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    notifications = [
        {
            'id': n.id,
            'notification_id': n.notification_id,
            'message': n.notification.message,
            'viewed': n.viewed,
            'sent_at': n.sent_at.isoformat() if n.sent_at else None,
            'news_id': n.notification.news_id,
            'news_title': n.notification.news.title if n.notification.news else None
        }
        for n in pagination.items
    ]
    return jsonify({
        'notifications': notifications,
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages
    }), 200

@notification_routes.route('/notifications/<int:notification_id>/viewed', methods=['POST'])
@token_required
def mark_notification_viewed(notification_id):
    user = getattr(request, 'user', None)
    if not user:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    n = UserNotification.query.filter_by(id=notification_id, user_id=user.id).first()
    if not n:
        return jsonify({'error': 'Notificação não encontrada'}), 404
    n.viewed = True
    db.session.commit()
    return jsonify({'success': True}), 200


@notification_routes.route('/notifications/mark_all_read', methods=['POST'])
@token_required
def mark_all_read():
    user = getattr(request, 'user', None)
    if not user:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    UserNotification.query.filter_by(user_id=user.id, viewed=False).update({"viewed": True})
    db.session.commit()
    return jsonify({'success': True}), 200


@notification_routes.route('/notifications/clear', methods=['POST'])
@token_required
def clear_notifications():
    user = getattr(request, 'user', None)
    if not user:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    # Remove only the user's notification links; keep Notification records (audit) if desired
    UserNotification.query.filter_by(user_id=user.id).delete()
    db.session.commit()
    return jsonify({'success': True}), 200