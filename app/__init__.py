from flask import Flask
from .extension import db, login_manager, mail
from flask_migrate import Migrate
from .config import config_dict

migrate = Migrate()

def create_app(config_name="development"):
    app = Flask(__name__)

    # Load config (development by default)
    app.config.from_object(config_dict[config_name])

    # --- Init extensions ---
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "main.login"
    mail.init_app(app)

    # --- User loader ---
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.query.get(int(user_id))

    # --- Blueprints ---
    from .routes import main
    app.register_blueprint(main)

    return app