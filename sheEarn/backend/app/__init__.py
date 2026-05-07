"""
SheEarn Application Factory
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_migrate import Migrate

from config import config

# Extension instances
db = SQLAlchemy()
jwt = JWTManager()
socketio = SocketIO(async_mode='gevent')
migrate = Migrate()


def create_app(config_name="default"):
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config[config_name])

    # Ensure upload folder exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    CORS(app, origins=app.config["CORS_ORIGINS"], supports_credentials=True)
    socketio.init_app(
        app,
        cors_allowed_origins="*",
        async_mode="gevent",
        logger=False,
        engineio_logger=False,
    )
    migrate.init_app(app, db)

    # Cloudinary setup
    if app.config.get("USE_CLOUDINARY"):
        import cloudinary
        cloudinary.config(
            cloud_name=app.config["CLOUDINARY_CLOUD_NAME"],
            api_key=app.config["CLOUDINARY_API_KEY"],
            api_secret=app.config["CLOUDINARY_API_SECRET"],
        )

    # Register blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.profile_routes import profile_bp
    from app.routes.service_routes import service_bp
    from app.routes.booking_routes import booking_bp
    from app.routes.payment_routes import payment_bp
    from app.routes.rating_routes import rating_bp
    from app.routes.scheme_routes import scheme_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.chat_routes import chat_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(profile_bp, url_prefix="/api/profile")
    app.register_blueprint(service_bp, url_prefix="/api/services")
    app.register_blueprint(booking_bp, url_prefix="/api/bookings")
    app.register_blueprint(payment_bp, url_prefix="/api/payments")
    app.register_blueprint(rating_bp, url_prefix="/api/ratings")
    app.register_blueprint(scheme_bp, url_prefix="/api/schemes")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(chat_bp, url_prefix="/api/chat")

    # Register SocketIO events
    from app.routes import socket_events  # noqa: F401

    # Health check
    @app.route("/api/health")
    def health():
        return {"status": "ok", "app": "SheEarn", "version": "1.0.0"}

    # Static file serving for uploads
    from flask import send_from_directory

    @app.route("/uploads/<path:filename>")
    def serve_upload(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    # Serve frontend files from ../frontend
    import os as _os
    _frontend_dir = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", "..", "frontend"))

    @app.route("/<path:filename>")
    def serve_frontend(filename):
        return send_from_directory(_frontend_dir, filename)

    @app.route("/")
    def serve_index():
        return send_from_directory(_frontend_dir, "index.html")

    return app
