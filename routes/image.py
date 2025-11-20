from flask import Blueprint, request, jsonify, current_app
from services.image_service import save_image
from routes.decorators import token_required  # remove/temporariamente comente se estiver testando sem token

image_routes = Blueprint('image_routes', __name__)

@image_routes.route('/upload-image', methods=['POST'])
@token_required
def upload_image():
    # DEBUG: inspeciona o conteúdo da requisição para entender por que request.files está vazio
    current_app.logger.debug("Content-Type: %s", request.content_type)
    current_app.logger.debug("request.files keys: %s", list(request.files.keys()))
    current_app.logger.debug("request.form keys: %s", list(request.form.keys()))

    # aceita nomes comuns: 'image' ou 'file'
    file = request.files.get('image') or request.files.get('file')

    if not file:
        return jsonify({
            'success': False,
            'error': 'Nenhum arquivo recebido. Verifique: body=form-data, campo tipo File e nome da chave "image".',
            'debug': {
                'content_type': request.content_type,
                'files': list(request.files.keys()),
                'form': list(request.form.keys())
            }
        }), 400

    try:
        url = save_image(file)
        return jsonify({'success': True, 'url': url}), 200
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception:
        current_app.logger.exception('Erro ao salvar imagem')
        return jsonify({'success': False, 'error': 'Erro interno'}), 500