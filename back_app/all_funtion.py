# app/all_funtion.py ke andar

from flask import redirect, url_for, flash
from flask_login import current_user
from .models import *
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
import os
import uuid
from flask import current_app


def create_admin_user():
    # Check if admin already exists
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        hashed_password = generate_password_hash('Ehtesham@admin-2024')
        admin = User(
            full_name='Ehtesham Aalam (Admin)',
            email='23f2001511@ds.study.iitm.ac.in',
            password=hashed_password,
            phone_number='0000000000',
            age=22,
            gender='Male',
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


def save_upload(file_storage, subfolder='uploads', allowed_ext=None, max_bytes=None):
    """Validate and save an uploaded file. Returns the stored filename or None."""
    if file_storage is None or not file_storage.filename:
        return None

    if allowed_ext is None:
        allowed_ext = current_app.config['ALLOWED_UPLOAD_EXTENSIONS']

    original_name = file_storage.filename
    ext = original_name.rsplit('.', 1)[-1].lower() if '.' in original_name else ''

    if ext not in allowed_ext:
        return None

    if max_bytes is not None:
        file_storage.stream.seek(0, os.SEEK_END)
        size = file_storage.stream.tell()
        file_storage.stream.seek(0)
        if size > max_bytes:
            return None

    safe_name = secure_filename(original_name)
    unique_name = f"{uuid.uuid4().hex}_{safe_name}" if safe_name else f"{uuid.uuid4().hex}.{ext}"

    folder = os.path.join(current_app.root_path, 'static', subfolder)
    os.makedirs(folder, exist_ok=True)

    file_storage.save(os.path.join(folder, unique_name))
    return unique_name


def create_notification(recipient_id, title, message, link=None):
    """Create an in-app notification for a user."""
    notif = Notification(
        recipient_id=recipient_id,
        title=title,
        message=message,
        link=link
    )
    db.session.add(notif)
    db.session.flush()

    try:
        from flask_socketio import emit
        from app import socketio
        socketio.emit(
            'notification',
            {
                'id': notif.id,
                'title': notif.title,
                'message': notif.message,
                'link': notif.link or '',
                'created_at': notif.created_at.strftime('%Y-%m-%d %H:%M') if notif.created_at else ''
            },
            room=f'user_{recipient_id}'
        )
    except Exception:
        pass

    return notif


def notify_other_party(appointment, title, message, link=None):
    """Notify the doctor and patient involved in an appointment (excluding sender)."""
    parties = []
    if appointment.doctor and appointment.doctor.user_id != current_user.id:
        parties.append(appointment.doctor.user_id)
    if appointment.patient and appointment.patient.user_id != current_user.id:
        parties.append(appointment.patient.user_id)

    created = []
    for uid in set(parties):
        created.append(create_notification(uid, title, message, link))
    return created
