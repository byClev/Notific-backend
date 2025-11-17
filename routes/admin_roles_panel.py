# admin_roles_panel.py (ATUALIZADO)

from flask import Blueprint, jsonify, render_template, request, current_app
import jwt
from routes.decorators import token_required, role_required
from app import db
# Importe o Modelo e o Enum do seu arquivo
from models.userModel import User, RoleEnum 

admin_roles_panel = Blueprint('admin_roles_panel', __name__)

# --- ROTA PARA RENDERIZAR A PÁGINA HTML ---
@admin_roles_panel.route('/admin/roles/view', methods=['GET'])
@role_required('ADMIN')
@token_required
def admin_roles_view():
    """ (ROTA 1/4) Renderiza a página 'admin_roles.html'. """
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
    return render_template('admin_roles.html', usuario=usuario)


# --- ROTAS DA API PARA AS LISTAS ---

@admin_roles_panel.route('/admin/api/lista_admins', methods=['GET'])
@role_required('ADMIN')
@token_required
def get_admin_list():
    """ (ROTA 2/4 - NOVA) Retorna usuários com o role ADMIN. """
    try:
        users = User.query.filter(User.role == RoleEnum.ADMIN).all()
        return jsonify([user.to_dict() for user in users]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_roles_panel.route('/admin/api/lista_moderadores', methods=['GET'])
@role_required('ADMIN')
@token_required
def get_moderador_list():
    """ (ROTA 3/4 - ANTIGA, RENOMEADA) Retorna usuários com o role MODERADOR. """
    try:
        users = User.query.filter(User.role == RoleEnum.MODERADOR).all()
        return jsonify([user.to_dict() for user in users]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_roles_panel.route('/admin/api/lista_pendentes', methods=['GET'])
@role_required('ADMIN')
@token_required
def get_pendentes_list():
    """ (ROTA 4/4 - ANTIGA, RENOMEADA) Retorna usuários com o role PENDENTE_MOD. """
    try:
        users = User.query.filter(User.role == RoleEnum.PENDENTE_MOD).all()
        return jsonify([user.to_dict() for user in users]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

#
# --- NOTAS IMPORTANTES ---
# A Rota de BUSCA (/admin/api/search-user) 
# e a Rota de MUDANÇA (/admin/change-role) 
# já existem no seu outro arquivo (admin_panel.py) e serão usadas pelo 
# nosso novo JavaScript. Não precisamos recriá-las aqui.
#