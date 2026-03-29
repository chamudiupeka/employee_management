from flask import Flask

from .config import Config
from .db import init_app as init_db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    init_db(app)

    from .blueprints.home import home_bp
    from .blueprints.employees import employees_bp

    app.register_blueprint(home_bp)
    app.register_blueprint(employees_bp, url_prefix="/employees")

    return app
