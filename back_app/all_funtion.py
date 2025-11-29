# app/all_funntion.py ke andar

from flask import redirect, url_for, flash
from flask_login import current_user
from .models import *
from werkzeug.security import generate_password_hash
import os
from flask import current_app




def create_admin_user():
    # Check if admin already exists
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        hashed_password = generate_password_hash('Admin@2024')
        admin = User(
            full_name='Ehtesham Aalam (Admin)',
            email='Ehtesham@hms.com',
            password=hashed_password,
            phone_number='0000000000',
            age = 22,
            gender = 'Male',
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully!")
    else:
        print("Admin user already exists.")



def save_picture(form_picture):
    # Picture ko save karne ka logic...
    filename = form_picture.filename
    picture_path = os.path.join(current_app.root_path, 'static/img', filename)
    form_picture.save(picture_path)
    return filename

