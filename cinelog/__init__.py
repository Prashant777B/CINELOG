import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "routes.login"

def create_app():
    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), "templates"))
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    from .models import User  # noqa

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except Exception:
            return None

    from .routes import bp as routes_bp
    app.register_blueprint(routes_bp)

    from .tmdb import bp as tmdb_bp
    app.register_blueprint(tmdb_bp)

    with app.app_context():
        db.create_all()

    @app.cli.command("init-db")
    def init_db():
        db.create_all()
        print("Initialized the database.")
    return app
