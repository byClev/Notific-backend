# routes/home.py

from flask import Blueprint, request, jsonify, render_template
from routes.decorators import token_required

home_routes = Blueprint('home_routes', __name__)

@home_routes.route('/', methods=['GET'])
def home():
    # Render the frontend home page template
    return render_template('home.html')

@home_routes.route('/status', methods=['GET'])
@token_required
def status():
    return jsonify({"status": "ok"}), 200