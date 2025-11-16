from flask import Flask
from flask_swagger_ui import get_swaggerui_blueprint

from  .routes.user_route import auth_bp
from .routes.dailyLogs_route import food_bp
from .extensions import mongo
from  .config import Config


def create_app():
    app = Flask(__name__)
    
    app.config.from_object(Config.Config)

    mongo.init_app(app)


    app.register_blueprint(auth_bp)
    app.register_blueprint(food_bp)

    return app
