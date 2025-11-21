#app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from flask_migrate import Migrate
from flask_mail import Mail
from sqlalchemy import text
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit

db = SQLAlchemy()
migrate = Migrate()
mail = Mail()

def create_app():
    load_dotenv()

    app = Flask(__name__, template_folder='../../html', static_folder='../../static')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config.setdefault('MAX_CONTENT_LENGTH', 10 * 1024 * 1024)  # 10 MB por upload
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
    
    mail.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)

    from routes.home import home_routes
    from routes.user import user_routes
    from routes.auth import auth_routes
    from routes.news import news_routes
    from routes.notification import notification_routes
    from routes.admin_panel import admin_panel
    from routes.admin_roles_panel import admin_roles_panel
    from routes.image import image_routes
    
    app.register_blueprint(home_routes)
    app.register_blueprint(user_routes)
    app.register_blueprint(auth_routes)
    app.register_blueprint(news_routes)
    app.register_blueprint(notification_routes)
    app.register_blueprint(admin_panel)
    app.register_blueprint(admin_roles_panel)
    app.register_blueprint(image_routes)
    
    from services.cleanup_service import cleanup_rejected_news
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=cleanup_rejected_news, trigger=IntervalTrigger(days=7), id='cleanup_rejected_news', name='Cleanup rejected news')
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())
    
    return app