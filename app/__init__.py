from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_name="development"):
    app = Flask(__name__, template_folder="../templates", static_folder="../static")

    # Load config
    from app.config import config
    app.config.from_object(config[config_name])

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.items import items_bp
    from app.routes.requests import requests_bp
    from app.routes.wanted import wanted_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.main import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(items_bp, url_prefix="/items")
    app.register_blueprint(requests_bp, url_prefix="/requests")
    app.register_blueprint(wanted_bp, url_prefix="/wanted")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")

    return app
