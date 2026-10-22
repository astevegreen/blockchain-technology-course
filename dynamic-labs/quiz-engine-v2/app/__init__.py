from pathlib import Path

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from .auth import init_shared_auth
from .config import load_config
from .db import init_app as init_db_app
from .expiration_worker import init_app as init_expiration_worker_app
from .students import init_app as init_students_app
from .blueprints.health import bp as health_bp
from .blueprints.instructor import bp as instructor_bp
from .blueprints.student import bp as student_bp


def create_app(config_overrides=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(load_config())
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    if config_overrides:
        app.config.update(config_overrides)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError(
            "QUIZ_ENGINE_SECRET_KEY is not set. Run ./lab-manager.sh deploy, which "
            "generates it into .runtime/runtime-secrets.env, or set it yourself."
        )

    database_path = app.config["DATABASE_PATH"]
    if database_path != ":memory:":
        Path(database_path).expanduser().parent.mkdir(parents=True, exist_ok=True)

    init_db_app(app)
    init_students_app(app)
    init_expiration_worker_app(app)
    init_shared_auth(app)
    app.register_blueprint(health_bp)
    app.register_blueprint(instructor_bp)
    app.register_blueprint(student_bp)

    return app
