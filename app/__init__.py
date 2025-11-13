#app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from flask_migrate import Migrate
from flask_mail import Mail
from sqlalchemy import text

db = SQLAlchemy()
migrate = Migrate()
mail = Mail()

def create_app():
    load_dotenv()

    app = Flask(__name__, template_folder='../../html', static_folder='../../static')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
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

    # Ensure new image columns exist in the `news` table to avoid ProgrammingError
    # Uses Postgres `ADD COLUMN IF NOT EXISTS` so it's safe to run multiple times.
    try:
        with app.app_context():
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE news ADD COLUMN IF NOT EXISTS img VARCHAR(400)"))
                conn.execute(text("ALTER TABLE news ADD COLUMN IF NOT EXISTS imagem_banner VARCHAR(400)"))
                # commit if the DB requires it
                conn.commit()
    except Exception as e:
        # don't prevent app startup; log for debugging
        try:
            app.logger.exception('Failed to ensure news image columns')
        except Exception:
            print('Failed to ensure news image columns:', e)

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