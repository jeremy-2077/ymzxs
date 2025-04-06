from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO()
jwt = JWTManager()

def create_app(config_class='config.Config'):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    socketio.init_app(app, cors_allowed_origins="*")
    jwt.init_app(app)
    
    # 注册蓝图
    from app.routes.auth import auth_bp
    from app.routes.user import user_bp
    from app.routes.seat import seat_bp
    from app.routes.facility import facility_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(user_bp, url_prefix='/api/user', name='user_singular')
    app.register_blueprint(seat_bp, url_prefix='/api/seats')
    app.register_blueprint(facility_bp, url_prefix='/api/facilities')
    
    return app 