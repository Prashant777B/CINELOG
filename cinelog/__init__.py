import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)

    # Security & database
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "fallback_key_change_in_production")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///cinelog.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Load TMDB key
    app.config["TMDB_API_KEY"] = os.getenv("TMDB_API_KEY")
    if not app.config["TMDB_API_KEY"]:
        print("⚠️  WARNING: TMDB_API_KEY not found in environment variables!")
    else:
        print("✓ TMDB_API_KEY loaded successfully")

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "routes.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"

    # Import models here so user_loader can find User
    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from .routes import bp as routes_bp
    from .tmdb import bp as tmdb_bp
    app.register_blueprint(routes_bp)
    app.register_blueprint(tmdb_bp)

    # Create tables if missing
    with app.app_context():
        db.create_all()

    return app
