from flask_socketio import join_room, leave_room, emit
from flask import request
from flask_login import current_user
from .models import db, ChatMessage, Notification
from .all_funtion import create_notification
import os


def register_socketio_events(socketio):
    @socketio.on('connect')
    def handle_connect(auth=None):
        if current_user.is_authenticated:
            join_room(f'user_{current_user.id}')

    @socketio.on('disconnect')
    def handle_disconnect():
        if current_user.is_authenticated:
            leave_room(f'user_{current_user.id}')

    @socketio.on('join_appointment_room')
    def handle_join_room(data):
        appointment_id = data.get('appointment_id')
        if not current_user.is_authenticated:
            return
        join_room(f'appointment_{appointment_id}')
        # Mark all previous messages as read for this user
        mark_read(appointment_id)

    @socketio.on('typing')
    def handle_typing(data):
        if not current_user.is_authenticated:
            return
        appointment_id = data.get('appointment_id')
        emit('typing', {'user_id': current_user.id,
                        'name': current_user.full_name,
                        'is_typing': data.get('is_typing', True)},
             room=f'appointment_{appointment_id}', include_self=False)

    @socketio.on('send_message')
    def handle_send_message(data):
        if not current_user.is_authenticated:
            return
        appointment_id = data.get('appointment_id')
        message_text = (data.get('message') or '').strip()
        file_url = data.get('file_url') or None
        file_name = data.get('file_name') or None

        from .models import Appointment
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return
        if not is_participant(appointment):
            return

        if not message_text and not file_url:
            return

        msg = ChatMessage(
            appointment_id=appointment_id,
            sender_id=current_user.id,
            message=message_text or None,
            file_url=file_url,
            file_name=file_name
        )
        db.session.add(msg)
        db.session.commit()

        payload = {
            'id': msg.id,
            'appointment_id': appointment_id,
            'sender_id': current_user.id,
            'sender_name': current_user.full_name,
            'message': msg.message,
            'file_url': file_url,
            'file_name': file_name,
            'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S') if msg.created_at else ''
        }
        emit('new_message', payload, room=f'appointment_{appointment_id}')

        # Notify the other party via notification system
        from .all_funtion import notify_other_party
        link = f'/chat/{appointment_id}'
        notify_other_party(appointment,
                           'New message',
                           f'{current_user.full_name} sent you a message.',
                           link)

    @socketio.on('mark_read')
    def handle_mark_read(data):
        appointment_id = data.get('appointment_id')
        if not current_user.is_authenticated:
            return
        mark_read(appointment_id)


def mark_read(appointment_id):
    if not current_user.is_authenticated:
        return
    messages = ChatMessage.query.filter(
        ChatMessage.appointment_id == appointment_id,
        ChatMessage.sender_id != current_user.id,
        ChatMessage.is_read.is_(False)
    ).all()
    for m in messages:
        m.is_read = True
    if messages:
        db.session.commit()


def is_participant(appointment):
    if current_user.role.lower() == 'admin':
        return True
    if current_user.role.lower() == 'doctor':
        return appointment.doctor_id == current_user.doctor.id
    if current_user.role.lower() == 'patient':
        return appointment.patient_id == current_user.patient.id
    return False
