from flask import Blueprint, request, jsonify, render_template, current_app
import jwt
from routes.decorators import token_required, role_required
from app import db
from models.userModel import User
from models.newsModel import News, StatusEnum, TagEnum

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
    """Return JSON list of pending news (API endpoint).
    The HTML view is provided by `/admin/news/pending/view`.
    """
    items = News.query.filter(News.status == StatusEnum.PENDENTE).order_by(News.created_at.asc()).all()
    return jsonify([n.to_dict() for n in items]), 200


@admin_panel.route('/admin/news/pending/view', methods=['GET'])
@role_required(['ADMIN', 'MODERATOR'])
@token_required
def list_pending_news_view():
    """Render `pedidos_pendentes.html` for browser access. Access restricted to ADMIN/MODERATOR.
    Injects `usuario` when a valid access_token cookie is present (same behavior as other server-rendered pages).
    """
    items = News.query.filter(News.status == StatusEnum.PENDENTE).order_by(News.created_at.asc()).all()

    # Inject usuario like other server-rendered pages
    usuario = None
    token = request.cookies.get('access_token')
    if token:
        try:
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            user = User.query.get(payload.get('user_id'))
            if user:
                usuario = user.to_dict()
        except Exception:
            usuario = None

    return render_template('pedidos_pendentes.html', usuario=usuario)


@admin_panel.route('/admin/news/<int:news_id>/approve', methods=['POST'])
@role_required(['ADMIN', 'MODERATOR'])
@token_required
def approve_news(news_id):
    n = News.query.get(news_id)
    if not n:
        return jsonify({'error': 'Notícia não encontrada'}), 404
    # Allow caller to set hotNews and tags when approving via JSON payload { hot: true, tags: [...] }
    payload = request.get_json(silent=True) or {}
    try:
        n.hotNews = bool(payload.get('hot', n.hotNews))
    except Exception:
        pass

    # parse tags if provided (accept list or comma-separated string)
    tags_payload = payload.get('tags')
    if tags_payload is not None:
        parsed = []
        try:
            if isinstance(tags_payload, list):
                candidates = tags_payload
            else:
                candidates = [t.strip() for t in str(tags_payload).split(',') if t.strip()]
            for t in candidates:
                try:
                    if isinstance(t, str):
                        key = t.strip().upper()
                        if key in TagEnum.__members__:
                            parsed.append(TagEnum[key])
                        else:
                            # try value
                            parsed.append(TagEnum(key))
                    else:
                        parsed.append(t)
                except Exception:
                    # ignore invalid tag values
                    continue
        except Exception:
            parsed = []

        if parsed:
            n.tags = parsed

    n.status = StatusEnum.ACEITA
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
    db.session.commit()
    return jsonify(n.to_dict()), 200


@admin_panel.route('/admin/news/<int:news_id>/set_pending', methods=['POST'])
@role_required(['ADMIN', 'MODERATOR'])
@token_required
def set_news_pending(news_id):
    n = News.query.get(news_id)
    if not n:
        return jsonify({'error': 'Notícia não encontrada'}), 404
    n.status = StatusEnum.PENDENTE
    db.session.commit()
    return jsonify(n.to_dict()), 200


@admin_panel.route('/admin/news/<int:news_id>/set_hot', methods=['POST'])
@role_required(['ADMIN', 'MODERATOR'])
@token_required
def set_news_hot(news_id):
    n = News.query.get(news_id)
    if not n:
        return jsonify({'error': 'Notícia não encontrada'}), 404
    payload = request.get_json(silent=True) or {}
    try:
        n.hotNews = bool(payload.get('hot', True))
    except Exception:
        n.hotNews = True
    db.session.commit()
    return jsonify(n.to_dict()), 200


@admin_panel.route('/admin/news/<int:news_id>/update-tags', methods=['POST'])
@role_required(['ADMIN', 'MODERATOR'])
@token_required
def update_news_tags(news_id):
    n = News.query.get(news_id)
    if not n:
        return jsonify({'error': 'Notícia não encontrada'}), 404
    payload = request.get_json(silent=True) or {}
    tags_payload = payload.get('tags')
    parsed = []
    if tags_payload is not None:
        try:
            if isinstance(tags_payload, list):
                candidates = tags_payload
            else:
                candidates = [t.strip() for t in str(tags_payload).split(',') if t.strip()]
            for t in candidates:
                try:
                    if isinstance(t, str):
                        key = t.strip().upper()
                        if key in TagEnum.__members__:
                            parsed.append(TagEnum[key])
                        else:
                            # try value
                            parsed.append(TagEnum(key))
                    else:
                        parsed.append(t)
                except Exception:
                    continue
        except Exception:
            parsed = []

    if parsed:
        n.tags = parsed
        db.session.commit()
    return jsonify(n.to_dict()), 200


@admin_panel.route('/admin/news/<int:news_id>/delete', methods=['DELETE'])
@role_required(['ADMIN', 'MODERATOR'])
@token_required
def delete_news_admin(news_id):
    n = News.query.get(news_id)
    if not n:
        return jsonify({'error': 'Notícia não encontrada'}), 404
    # Delete notifications linked to this news first
    from models.notificationModel import Notification
    Notification.query.filter_by(news_id=news_id).delete()
    db.session.delete(n)
    db.session.commit()
    return jsonify({'message': 'Notícia removida'}), 200


# Dev-only diagnostic route: inspect access_token cookie and decoded payload
@admin_panel.route('/admin/debug/token', methods=['GET'])
def debug_token():
    # Only allow in debug mode to avoid leaking token info in production
    if not current_app.debug:
        return jsonify({'error': 'Not Found'}), 404

    token = request.cookies.get('access_token')
    info = {'cookie_present': bool(token)}
    if token:
        try:
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            info['decoded'] = payload
        except Exception as e:
            info['decode_error'] = str(e)
    return jsonify(info), 200

# Em /routes/admin_panel.py
from sqlalchemy import or_ # Importe o 'or_' do SQLAlchemy no topo

# ... (resto do seu admin_panel.py) ...

@admin_panel.route('/admin/api/search-user', methods=['GET'])
@role_required(['ADMIN', 'MODERATOR']) # Apenas admins/mods podem buscar
@token_required
def search_user_api():
    """
    (NOVA ROTA)
    Busca um usuário por ID, username ou e-mail e retorna seu JSON.
    """
    termo = request.args.get('termo')
    if not termo:
        return jsonify({'error': 'Termo de busca ausente'}), 400

    user = None
    
    # 1. Tenta buscar por ID se for um número
    if termo.isdigit():
        user = User.query.get(int(termo))

    # 2. Se não achou por ID, tenta por username ou e-mail
    if not user:
        # Usamos 'ilike' para busca case-insensitive (ignorando maiúsculas/minúsculas)
        user = User.query.filter(
            or_(
                User.username.ilike(f'%{termo}%'),
                User.email.ilike(f'%{termo}%')
            )
        ).first() # Pega o primeiro resultado

    # 3. Se não encontrou ninguém
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    # Se encontrou, retorna o JSON do usuário
    return jsonify(user.to_dict()), 200