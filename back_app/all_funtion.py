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

# def admin_required(f):
#     """
#     Yeh decorator check karta hai ki user admin hai ya nahin.
#     Agar nahin, to use home page par bhej deta hai.
#     """
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if not current_user.is_authenticated or current_user.role.lower() != 'admin':
#             flash('Access Denied: You do not have permission to view this page.', 'danger')
#             return redirect(url_for('home')) # home function routes.py mein hai
#         return f(*args, **kwargs)
#     return decorated_function




def save_picture(form_picture):
    # Picture ko save karne ka logic...
    filename = form_picture.filename
    picture_path = os.path.join(current_app.root_path, 'static/img/profile_pics', filename)
    form_picture.save(picture_path)
    return filename

