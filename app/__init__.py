import os
from flask import Flask
from .config import config_by_name
from .extensions import db, login_manager


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    config_key = config_name or os.environ.get("FLASK_ENV", "development")
    app.config.from_object(config_by_name.get(config_key, config_by_name["development"]))

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    from .auth.routes import auth_bp
    from .dashboard.routes import dashboard_bp
    from .predict.routes import predict_bp
    from .reports.routes import reports_bp
    from .analytics.routes import analytics_bp
    from .about.routes import about_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(predict_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(about_bp)

    @app.route("/")
    def index():
        from flask import redirect, url_for

        return redirect(url_for("dashboard.index"))

    return app


