#app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from flask_migrate import Migrate
from flask_mail import Mail

db = SQLAlchemy()
migrate = Migrate()
mail = Mail()

def create_app():
    load_dotenv()

    app = Flask(__name__, template_folder='../../html', static_folder='../../static')
    # Load database URL: prefer explicit DATABASE_URL, but if it contains
    # unresolved placeholders (like ${DB_USER}) or is missing, build it from
    # individual DB_* env vars to avoid passing a malformed string to SQLAlchemy
    raw_db_url = os.getenv("DATABASE_URL") or ""
    if "${" in raw_db_url or not raw_db_url:
        db_user = os.getenv('DB_USER') or ''
        db_password = os.getenv('DB_PASSWORD') or ''
        db_host = os.getenv('DB_HOST') or 'localhost'
        db_port = os.getenv('DB_PORT') or '5432'
        db_name = os.getenv('DB_NAME') or ''
        db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    else:
        db_url = raw_db_url
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    
    mail.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)

    from routes.home import home_routes
    from routes.user import user_routes
    from routes.auth import auth_routes
    from routes.news import news_routes
    from routes.notification import notification_routes
    from routes.admin_panel import admin_panel

    app.register_blueprint(home_routes)
    app.register_blueprint(user_routes)
    app.register_blueprint(auth_routes)
    app.register_blueprint(news_routes)
    app.register_blueprint(notification_routes)
    app.register_blueprint(admin_panel)

    return app