from flask import Flask
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_wtf import CSRFProtect
from flask_mail import Mail
from back_app.models import db, User
import os

from dotenv import load_dotenv

load_dotenv()

socketio = SocketIO()
csrf = CSRFProtect()
mail = Mail()

login_manager = LoginManager()


def create_app():
    app = Flask(__name__)

    database_url = os.environ.get('DATABASE_URL', 'sqlite:///hospital_management.db')
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['WTF_CSRF_TIME_LIMIT'] = None

    # Uploads
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB global cap
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    app.config['ALLOWED_IMAGE_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    app.config['ALLOWED_UPLOAD_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp',
                                               'pdf', 'doc', 'docx', 'txt'}

    # Mail configuration
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'false').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER',
                                                       os.environ.get('MAIL_USERNAME'))

    # SocketIO config
    app.config['SOCKETIO_MESSAGE_QUEUE'] = None

    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    db.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    socketio.init_app(app, cors_allowed_origins='*')

    with app.app_context():
        from back_app.routes import main
        from back_app.socketio_events import register_socketio_events
        from back_app.all_funtion import create_admin_user
        app.register_blueprint(main)
        register_socketio_events(socketio)
        db.create_all()
        create_admin_user()

    # Custom error handlers
    @app.context_processor
    def inject_globals():
        from datetime import datetime as _dt
        return {'now_utc_year': _dt.utcnow().year}

    @app.errorhandler(404)
    def not_found(error):
        return render_template_safe('errors/404.html', code=404), 404

    @app.errorhandler(500)
    def server_error(error):
        return render_template_safe('errors/500.html', code=500), 500

    @app.errorhandler(413)
    def too_large(error):
        from flask import flash, redirect, url_for, request
        flash('File too large. Maximum allowed size is 16 MB.', 'danger')
        return redirect(request.referrer or url_for('main.home'))

    return app


def render_template_safe(template, **context):
    from flask import render_template
    try:
        return render_template(template, **context)
    except Exception:
        return ('<html><body style="font-family:sans-serif;text-align:center;padding:80px;">'
                '<h1>%s</h1><p>Something went wrong on our side.</p></body></html>' % context.get('code', 500)), context.get('code', 500)


app = create_app()

if __name__ == '__main__':
    socketio.run(app, debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
