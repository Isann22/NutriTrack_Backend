from flask import Flask

from  .routes.auth_route import auth_bp
from .routes.user_route import user_bp
from .routes.dailyLogs_route import food_bp
from .extensions import mongo,bcrypt,jwt
from  .config import Config


def create_app():
    app = Flask(__name__)
    
    app.config.from_object(Config.Config)

    mongo.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    


    app.register_blueprint(auth_bp)
    app.register_blueprint(food_bp)
    app.register_blueprint(user_bp)

    return app
