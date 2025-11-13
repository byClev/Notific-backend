from flask import Blueprint, request, jsonify
from routes.decorators import token_required, role_required
from app import db
from models.userModel import User
from models.newsModel import News, StatusEnum

admin_panel = Blueprint('admin_panel', __name__)

@admin_panel.route('/admin/change-role', methods=['POST'])
@role_required('ADMIN')
@token_required
def change_user_role():
    data = request.get_json()
    user_id = data.get('user_id')
    new_role = data.get('new_role')

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    user.role = new_role
    db.session.commit()
    return jsonify({'message': f'Role do usuário {user.username} alterada para {new_role}.'}), 200

@admin_panel.route('/admin/news/pending', methods=['GET'])
@role_required(['ADMIN', 'MODERATOR'])
@token_required
def list_pending_news():
    items = News.query.filter(News.status == StatusEnum.PENDENTE).order_by(News.created_at.asc()).all()
    return jsonify([n.to_dict() for n in items]), 200


@admin_panel.route('/admin/news/<int:news_id>/approve', methods=['POST'])
@role_required(['ADMIN', 'MODERATOR'])
@token_required
def approve_news(news_id):
    n = News.query.get(news_id)
    if not n:
        return jsonify({'error': 'Notícia não encontrada'}), 404
    n.status = StatusEnum.ACEITA
    n.active = True
    db.session.commit()
    # Notificar usuários quando notícia aprovada
    from services.notification_service import notify_users_for_news
    notify_users_for_news(n)
    return jsonify(n.to_dict()), 200


@admin_panel.route('/admin/news/<int:news_id>/reject', methods=['POST'])
@role_required(['ADMIN', 'MODERATOR'])
@token_required
def reject_news(news_id):
    n = News.query.get(news_id)
    if not n:
        return jsonify({'error': 'Notícia não encontrada'}), 404
    n.status = StatusEnum.REJEITADA
    n.active = False
    db.session.commit()
    return jsonify(n.to_dict()), 200