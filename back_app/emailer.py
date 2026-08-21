from flask import current_app
from flask_mail import Message
import logging

logger = logging.getLogger('hms.email')


def send_email(subject, recipients, body_html=None, body_text=None):
    """Send an email via Flask-Mail. Falls back to logging if SMTP is not configured."""
    mail = current_app.extensions.get('mail')
    username = current_app.config.get('MAIL_USERNAME')
    password = current_app.config.get('MAIL_PASSWORD')

    if mail is None or not username or not password:
        logger.info(
            "SMTP not configured - email would be sent.\n"
            "To: %s\nSubject: %s\nBody:\n%s",
            recipients, subject, body_html or body_text or ''
        )
        return False

    try:
        msg = Message(subject, recipients=recipients)
        if body_html:
            msg.html = body_html
        if body_text:
            msg.body = body_text
        mail.send(msg)
        return True
    except Exception as e:
        logger.error("Failed to send email: %s", e)
        logger.info("Email content fallback:\nTo: %s\nSubject: %s\nBody:\n%s",
                    recipients, subject, body_html or body_text or '')
        return False


def send_appointment_email(appointment, event):
    """Send appointment-related email (booked/confirmed/cancelled/completed)."""
    patient_email = appointment.patient.user.email
    doctor_email = appointment.doctor.user.email
    dt = appointment.appointment_datetime.strftime('%Y-%m-%d %H:%M') if appointment.appointment_datetime else 'N/A'
    doctor_name = f"Dr. {appointment.doctor.user.full_name}"
    patient_name = appointment.patient.user.full_name

    messages = {
        'booked': {
            'subject': f'Appointment Booked - {dt}',
            'html': f'<p>Dear <b>{patient_name}</b>,</p><p>Your appointment with <b>{doctor_name}</b> on <b>{dt}</b> has been booked successfully.</p><p>Thank you for choosing HMS Portal.</p>'
        },
        'confirmed': {
            'subject': f'Appointment Confirmed - {dt}',
            'html': f'<p>Dear <b>{patient_name}</b>,</p><p>Your appointment with <b>{doctor_name}</b> on <b>{dt}</b> has been confirmed.</p><p>Thank you for choosing HMS Portal.</p>'
        },
        'cancelled': {
            'subject': f'Appointment Cancelled - {dt}',
            'html': f'<p>Dear <b>{patient_name}</b>,</p><p>Your appointment with <b>{doctor_name}</b> on <b>{dt}</b> has been cancelled.</p><p>Please contact the hospital for rescheduling.</p>'
        },
        'completed': {
            'subject': f'Appointment Completed - {dt}',
            'html': f'<p>Dear <b>{patient_name}</b>,</p><p>Your appointment with <b>{doctor_name}</b> on <b>{dt}</b> has been marked as completed.</p><p>Your medical report is available in your dashboard.</p><p>Thank you for choosing HMS Portal.</p>'
        },
    }

    template = messages.get(event)
    if not template:
        return False

    # Notify patient
    send_email(template['subject'], [patient_email], body_html=template['html'])

    # Notify doctor on bookings/cancellations
    if event in ('booked', 'cancelled'):
        doctor_subject = f'Appointment {event.title()} - {patient_name}'
        doctor_html = f'<p>Dear <b>{doctor_name}</b>,</p><p>An appointment with <b>{patient_name}</b> on <b>{dt}</b> has been {event}.</p>'
        send_email(doctor_subject, [doctor_email], body_html=doctor_html)
