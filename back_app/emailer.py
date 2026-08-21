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
        print('\n' + '=' * 60)
        print('EMAIL NOT SENT (SMTP not configured) — would have emailed:')
        print('To:', recipients)
        print('Subject:', subject)
        print('Body:', (body_html or body_text or ''))
        print('=' * 60 + '\n')
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
        print('\n' + '=' * 60)
        print('EMAIL FAILED TO SEND (%s) — fallback content:' % e)
        print('To:', recipients)
        print('Subject:', subject)
        print('Body:', (body_html or body_text or ''))
        print('=' * 60 + '\n')
        return False


def send_doctor_credentials_email(doctor_name, email, generated_password, login_url='/'):
    """Email a newly created doctor their login credentials."""
    subject = 'Your HMS Portal Account Has Been Created'
    body_html = f"""
    <div style="font-family:Inter, Arial, sans-serif; max-width:520px; margin:0 auto;">
      <div style="background:#2563eb; padding:24px; border-radius:12px 12px 0 0; text-align:center;">
        <h2 style="color:#fff; margin:0;">Welcome to HMS Portal</h2>
      </div>
      <div style="border:1px solid #e2e8f0; border-top:none; padding:28px; border-radius:0 0 12px 12px;">
        <p style="color:#0f172a;">Dear <b>{doctor_name}</b>,</p>
        <p style="color:#475569;">Your doctor account has been created by the hospital administrator. You can sign in with the credentials below and complete your profile.</p>
        <div style="background:#f1f5f9; border-radius:8px; padding:16px; margin:20px 0;">
          <p style="margin:4px 0; color:#334155;"><b>Email:</b> {email}</p>
          <p style="margin:4px 0; color:#334155;"><b>Temporary Password:</b> <code style="background:#e2e8f0; padding:2px 8px; border-radius:4px; font-size:14px;">{generated_password}</code></p>
        </div>
        <p style="color:#475569;">After logging in, please go to <b>Profile Settings</b> to change your password and complete your details.</p>
        <a href="{login_url}" style="display:inline-block; background:#2563eb; color:#fff; text-decoration:none; padding:12px 24px; border-radius:8px; font-weight:600;">Login to HMS Portal</a>
        <p style="color:#94a3b8; font-size:12px; margin-top:24px;">If you didn't expect this email, please ignore it.</p>
      </div>
    </div>
    """
    return send_email(subject, [email], body_html=body_html)


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
