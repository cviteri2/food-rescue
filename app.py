from flask import Flask, redirect, url_for
from flask_login import LoginManager, current_user

from config import Config
from models import Usuario, db


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Inicia sesion para continuar."
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Usuario, int(user_id))

    from routes.admin import admin_bp
    from routes.api import api_bp
    from routes.auth import auth_bp
    from routes.comercios import comercios_bp
    from routes.organizaciones import organizaciones_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(comercios_bp)
    app.register_blueprint(organizaciones_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    @app.route("/")
    def index():
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if current_user.tipo == "comercio":
            return redirect(url_for("comercios.dashboard"))
        if current_user.tipo == "organizacion":
            return redirect(url_for("organizaciones.dashboard"))
        if current_user.tipo == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("auth.login"))

    return app


app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
