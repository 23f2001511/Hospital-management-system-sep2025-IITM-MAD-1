from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from back_app.models import db


app = None

def create_app():
    app = Flask(__name__ )
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital_management.db'
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


#initialise login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'


#Register loader funtion 
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    db.init_app(app)
    app.app_context().push()
    db.create_all()
    return app


app = create_app()
from back_app.routes import *

if __name__ == '__main__':
    app.run(debug=True)
