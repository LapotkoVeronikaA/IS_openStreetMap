# app/__init__.py
from flask import Flask
from .config import Config
from .extensions import db, migrate

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Инициализация расширений
    db.init_app(app)
    migrate.init_app(app, db)

    # Регистрация блюпринтов
    from .main import main_bp
    app.register_blueprint(main_bp)

    return app