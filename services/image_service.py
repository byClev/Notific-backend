import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app, url_for

ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_filename(filename: str) -> bool:
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return ext in ALLOWED_EXT

def save_image(file) -> str:
    """
    Salva o arquivo dentro de <static>/img/uploads e retorna a URL externa.
    Levanta ValueError para problemas do cliente.
    """
    if file is None or file.filename == '':
        raise ValueError('No file provided')
    if not allowed_filename(file.filename):
        raise ValueError('Invalid file type')

    filename = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    upload_folder = os.path.join(current_app.static_folder, 'img', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    path = os.path.join(upload_folder, unique_name)
    file.save(path)

    # Retorna URL completa (http(s)://host/static/img/uploads/...)
    return url_for('static', filename=f'img/uploads/{unique_name}', _external=True)