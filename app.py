from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from back_app.models import db, User
import os

app = None

def create_app():
    app = Flask(__name__)

    # ====== DATABASE CONFIG ======
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///hospital_management.db')
    
    # Render fix — postgres:// → postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    # ==============================

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_secret_key')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialise login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    # Register loader function
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    
    return app


app = create_app()
from back_app.routes import *

if __name__ == '__main__':
    app.run(debug=False)  # False for production