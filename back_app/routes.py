from flask import render_template, redirect, url_for, request, flash, jsonify, send_from_directory, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash , generate_password_hash
from werkzeug.utils import secure_filename
from datetime import time , datetime , date
from .models import *
from .all_funtion import save_picture  , create_admin_user , save_upload , create_notification , notify_other_party
from flask import Blueprint
import uuid
import os
from .emailer import send_appointment_email



main = Blueprint('main', __name__)


# =================================================================

@main.route('/')
def home():
    return render_template('home.html')


# =========================Authentication Routes==================


@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone_number = request.form.get('phone_number')
        age = request.form.get('age')
        gender = request.form.get('gender')
        role = request.form.get('role')

        # Server-side validation
        if not full_name or not email or not password or not phone_number:
            flash('All fields are required.', 'danger')
            return redirect(url_for('main.register'))
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return redirect(url_for('main.register'))
        if '@' not in email or '.' not in email:
            flash('Please enter a valid email address.', 'danger')
            return redirect(url_for('main.register'))
        try:
            if age is None or int(age) <= 0 or int(age) > 120:
                flash('Please enter a valid age between 1 and 120.', 'danger')
                return redirect(url_for('main.register'))
        except (TypeError, ValueError):
            flash('Please enter a valid age.', 'danger')
            return redirect(url_for('main.register'))
        if not phone_number.isdigit() or len(phone_number) < 10:
            flash('Please enter a valid 10-digit phone number.', 'danger')
            return redirect(url_for('main.register'))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please log in.', 'warning')
            return redirect(url_for('main.login'))

        new_user = User(
            full_name=full_name,
            email=email,
            password=generate_password_hash(password),  # Hashing should be done here
            phone_number=phone_number,
            age=age,
            gender=gender,
            role='Patient',
        )

        add_patient = Patient(
            user=new_user,
            gender = gender

            )

        db.session.add(new_user)
        db.session.add(add_patient)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('main.login'))
    return render_template("auth/register.html")


@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        role = request.form.get('role')
        password = request.form.get('password')
        if not email or not password or not role:
            flash('Please fill in email, password and role.', 'danger')
            return redirect(url_for('main.login'))
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('Invalid email or password according to your selected role.', 'danger')
            return redirect(url_for('main.login'))
        if user.is_deleted:
            flash('This account has been deactivated. Please contact the administrator.', 'danger')
            return redirect(url_for('main.login'))
        user_name = user.full_name
        if user and user.role.lower() == role.lower() and check_password_hash(user.password, password):
            login_user(user)
            if user.role.lower() == 'doctor' and user.doctor.is_active:
                flash('Welcome Doctor !', 'success')
                return redirect(url_for('main.doctor_dashboard'))
            elif user.role.lower() == 'patient' and user.patient.is_active:
                flash('Welcome to HMS!', 'success')
                return redirect(url_for('main.patient_dashboard'))
            elif user.role.lower() == 'admin':
                flash('Welcome Admin !', 'success')
                return redirect(url_for('main.admin_dashboard'))
            else:
                flash('Your account is blocked. Please contact the administrator.', 'danger')
                return redirect(url_for('main.login'))
            flash('Logged in successfully!', 'success')
        else:
           
            flash('Invalid email or password according to your selected role.', 'red')
            return redirect(url_for('main.login'))
    return render_template("auth/login.html")


@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))


@main.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        new_password = request.form.get('pass')
        confirm_password = request.form.get('c_pass')

        user = User.query.filter_by(email=email).first()
        if not user:
            flash("❌ Email not found!", "danger")
            return redirect(url_for('main.forgot_password'))

        if new_password != confirm_password:
            flash("⚠ New & Confirm password do not match!", "warning")
            return redirect(url_for('main.forgot_password'))

        hashed_new_password = generate_password_hash(new_password)
        user.password = hashed_new_password
        db.session.commit()

        flash("✅ Password reset successfully! Please log in.", "success")
        return redirect(url_for('main.login'))
    return render_template("auth/forgot_pass.html")

@main.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():

    if request.method == "POST":
        old_pass = request.form.get("old_password")
        new_pass = request.form.get("new_password")
        confirm_pass = request.form.get("confirm_password")

        # 1️ Old password verify
        if not check_password_hash(current_user.password, old_pass):
            flash("❌ Old password is incorrect!", "danger")
            return redirect(url_for('main.change_password'))

        # 2️ New password match check
        if new_pass != confirm_pass:
            flash("⚠ New & Confirm password do not match!", "warning")
            return redirect(url_for('main.change_password'))

        # 3️ Password update (hashing required)
        hashed_new_password = generate_password_hash(new_pass)
        current_user.password = hashed_new_password
        db.session.commit()

        flash("✅ Password updated successfully!", "success")
        return redirect(url_for('main.update_profile'))
    return render_template("auth/profile_setting.html")


@main.route("/appointment/update_status/<int:appointment_id>/<string:new_status>", methods=['GET', 'POST'])
@login_required
def update_appointment_status(appointment_id, new_status):

    valid_status = ["Completed", "Cancelled", "Booked"]

    if new_status not in valid_status:
        flash("Invalid status!", "danger")
        return redirect(request.referrer)

    appointment = Appointment.query.get_or_404(appointment_id)

    # Authorization: only admin, the assigned doctor, or the booking patient may change status
    role = current_user.role.lower()
    is_admin = role == 'admin'
    is_own_doctor = role == 'doctor' and hasattr(current_user, 'doctor') and appointment.doctor_id == current_user.doctor.id
    is_own_patient = role == 'patient' and hasattr(current_user, 'patient') and appointment.patient_id == current_user.patient.id
    if not (is_admin or is_own_doctor or is_own_patient):
        flash("Unauthorized access!", "danger")
        return redirect(url_for('main.home'))

    # Patients may only cancel; doctors may complete or cancel; admin may set any valid status
    if role == 'patient' and new_status != 'Cancelled':
        flash("Patients may only cancel appointments.", "danger")
        return redirect(request.referrer)

    old_status = appointment.status
    appointment.status = new_status
    db.session.commit()

    # Notifications
    title = f"Appointment {new_status}"
    message = f"Appointment with {appointment.doctor.user.full_name} on {appointment.appointment_datetime.strftime('%Y-%m-%d %H:%M')} is now {new_status}."
    recipients = set()
    recipients.add(appointment.patient.user_id)
    recipients.add(appointment.doctor.user_id)
    for uid in recipients:
        if uid != current_user.id:
            create_notification(uid, title, message, url_for('main.view_appointment', appointment_id=appointment.id))

    # Email notifications
    event = new_status.lower()
    try:
        send_appointment_email(appointment, event)
    except Exception as e:
        print('Email error:', e)

    flash(f"Appointment marked as {new_status}", "success")
    return redirect(request.referrer)


@main.route('/appointment/<int:appointment_id>')
@login_required
def view_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    role = current_user.role.lower()
    is_admin = role == 'admin'
    is_own_doctor = role == 'doctor' and hasattr(current_user, 'doctor') and appointment.doctor_id == current_user.doctor.id
    is_own_patient = role == 'patient' and hasattr(current_user, 'patient') and appointment.patient_id == current_user.patient.id
    if not (is_admin or is_own_doctor or is_own_patient):
        flash("Unauthorized access!", "danger")
        return redirect(url_for('main.home'))
    return render_template('appointment/details.html', appointment=appointment)



@main.route('/update_profile' , methods=['POST','GET'])
@login_required
def update_profile():
    if request.method == 'POST':
        user = User.query.get(current_user.id)
        user.full_name = request.form.get('full_name')

        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file.filename != '':
                allowed = current_app.config['ALLOWED_IMAGE_EXTENSIONS']
                ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
                if ext not in allowed:
                    flash("Invalid image format. Allowed: png, jpg, jpeg, gif, webp", "danger")
                    return redirect('update_profile')
                picture_file = save_picture(file)
                user.profile_picture = picture_file

       
        
        if current_user.role.lower() == 'patient':
            p_user = Patient.query.get(current_user.patient.id)
            dob_str = request.form.get('date_of_birth')
            if dob_str:
                # Converts '2003-02-23' to a real python date
                p_user.date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()

            p_user.gender = request.form.get('gender')
            p_user.address = request.form.get('address')
           

        elif current_user.role.lower() == 'doctor':
            d_user  = Doctor.query.get(current_user.doctor.id)
            user.phone_number = request.form.get('phone_number') or user.phone_number
            age_val = request.form.get('age')
            if age_val and age_val.isdigit():
                user.age = int(age_val)
            user.gender = request.form.get('gender') or user.gender
            d_user.specialization = request.form.get('specialization') or d_user.specialization
            exp_val = request.form.get('experience_years')
            if exp_val and exp_val.isdigit():
                d_user.experience_years = int(exp_val)
            d_user.qualification = request.form.get('qualification') or d_user.qualification
            d_user.bio = request.form.get('bio') or ''
        
        db.session.commit()
        
        flash("Your profile successfully , Updated!")
        return redirect('update_profile')
    else:

        user = User.query.get(current_user.id)

        return render_template('auth/profile_setting.html' , current_user=user)




# =============== Dashboard Routes ===============

@main.route('/doctor/dashboard')
@login_required
def doctor_dashboard():
    if current_user.role.lower() != 'doctor' or not current_user.doctor.is_active:
        flash('You are blocked or not Doctor, Access denied', 'danger')
        return redirect(url_for('main.login'))
    doctor = Doctor.query.get(current_user.doctor.id)
    appointments = Appointment.query.filter_by(doctor_id=doctor.id).order_by(Appointment.appointment_datetime.desc()).all()
    t_upcomming_appt = Appointment.query.filter(Appointment.doctor_id==doctor.id,Appointment.status=='booked').count()
    t_done_appt = Appointment.query.filter(Appointment.doctor_id==doctor.id,Appointment.status!='booked').count()

    # Feature 2: today's load
    today_booked = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.status != 'Cancelled',
        db.func.date(Appointment.appointment_datetime) == date.today()
    ).count()
    today_max = doctor.max_appointments_per_day or 20

    return render_template('doctor/dashboard.html' , user=current_user, appointments=appointments , t_upcomming_appt = t_upcomming_appt , t_done_appt = t_done_appt,
                           today_booked=today_booked, today_max=today_max)


@main.route('/patient/dashboard')
@login_required
def patient_dashboard():
    if current_user.role.lower() != 'patient' or not current_user.patient.is_active:
        flash('You are bloked or not Patient ,Access denied.', 'danger')
        return redirect(url_for('main.login'))
    
   
    departments = Department.query.all()
    appointments = Appointment.query.filter_by(patient_id=current_user.patient.id).all()
    upcoming_appointments_count = Appointment.query.filter(Appointment.patient_id==current_user.patient.id,Appointment.status=='booked').count()
    total_medical_record = 0
    for appt in appointments:
        if appt.status.lower() == 'completed':
            total_medical_record += 1

    # Next upcoming appointment for the slip card (Feature 3)
    next_upcoming = Appointment.query.filter(
        Appointment.patient_id == current_user.patient.id,
        Appointment.status == 'booked',
        Appointment.appointment_datetime >= datetime.now()
    ).order_by(Appointment.appointment_datetime.asc()).first()
    all_upcoming = Appointment.query.filter(
        Appointment.patient_id == current_user.patient.id,
        Appointment.status == 'booked'
    ).order_by(Appointment.appointment_datetime.asc()).all()

    return render_template('patient/dashboard.html' , user=current_user , departments=departments , appointments=appointments , upcoming_appointments_count=upcoming_appointments_count , total_medical_record=total_medical_record,
                           next_upcoming=next_upcoming, all_upcoming=all_upcoming)



@main.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role.lower() != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.home'))
    appointments = Appointment.query.order_by(Appointment.appointment_datetime.desc()).all()
    doctors = Doctor.query.join(User).filter(User.is_deleted.is_(False)).all()
    patients = Patient.query.all()
    total_appointments = Appointment.query.count()
    total_doctors = Doctor.query.join(User).filter(User.is_deleted.is_(False)).count()
    total_patients = Patient.query.count()

    # Appointments flagged as needing manual reassignment (Feature 1)
    needs_reassignment = Appointment.query.filter(
        Appointment.needs_reassignment.is_(True),
        Appointment.status != 'Cancelled'
    ).order_by(Appointment.appointment_datetime.asc()).all()
    reassignment_options = {}
    for appt in needs_reassignment:
        options = Doctor.query.join(User).filter(
            Doctor.department_id == appt.doctor.department_id,
            Doctor.id != appt.doctor_id,
            Doctor.is_active.is_(True),
            User.is_deleted.is_(False)
        ).all()
        reassignment_options[appt.id] = options

    # --- Analytics data (server-side, real queries) ---
    # 1. Appointments booked per day (last 14 days)
    from datetime import timedelta
    today = date.today()
    days = []
    counts = []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        days.append(d.strftime('%d %b'))
        counts.append(Appointment.query.filter(db.func.date(Appointment.appointment_datetime) == d).count())
    chart_appointments = {'labels': days, 'data': counts}

    # 2. Patient count by department (via doctors in each department -> their patients)
    dept_labels = []
    dept_data = []
    for dep in Department.query.all():
        dept_labels.append(dep.name)
        doctor_ids = [d.id for d in dep.doctors]
        if doctor_ids:
            count = Patient.query.join(Appointment, Appointment.patient_id == Patient.id)\
                .filter(Appointment.doctor_id.in_(doctor_ids)).distinct().count()
        else:
            count = 0
        dept_data.append(count)
    chart_dept_patients = {'labels': dept_labels, 'data': dept_data}

    # 3. Doctor workload (appointments handled)
    doc_labels = []
    doc_data = []
    for doc in Doctor.query.all():
        doc_labels.append(f"Dr. {doc.user.full_name[:12]}")
        doc_data.append(Appointment.query.filter_by(doctor_id=doc.id).count())
    chart_workload = {'labels': doc_labels, 'data': doc_data}

    # Status breakdown for a doughnut
    status_labels = ['Booked', 'Completed', 'Cancelled']
    status_data = [
        Appointment.query.filter_by(status='Booked').count(),
        Appointment.query.filter_by(status='Completed').count(),
        Appointment.query.filter_by(status='Cancelled').count(),
    ]

    return render_template('admin/dashboard.html', user=current_user, appointments=appointments,
                           doctors=doctors, patients=patients,
                           total_appointments=total_appointments, total_doctors=total_doctors,
                           total_patients=total_patients,
                           chart_appointments=chart_appointments,
                           chart_dept_patients=chart_dept_patients,
                           chart_workload=chart_workload,
                           status_labels=status_labels, status_data=status_data,
                           needs_reassignment=needs_reassignment,
                           reassignment_options=reassignment_options)





#========================= admin controller routes =========================


@main.route('/admin/doctors',methods=['GET'])
@login_required
def all_doctors():
    if current_user.role.lower() != 'admin':
        flash("you are nod admin access denied , DANGER!")
        return redirect(url_for('main.home'))
    page = request.args.get('page', 1, type=int)
    per_page = 8
    q = request.args.get('q', '').strip()
    department = request.args.get('department', '').strip()
    status = request.args.get('status', '').strip()

    query = Doctor.query.join(User, Doctor.user_id == User.id).join(Department, Doctor.department_id == Department.id).filter(User.is_deleted.is_(False))
    if q:
        like = f'%{q}%'
        query = query.filter(db.or_(User.full_name.ilike(like), User.email.ilike(like), Doctor.specialization.ilike(like)))
    if department:
        query = query.filter(Doctor.department_id == int(department))
    if status.lower() == 'active':
        query = query.filter(Doctor.is_active.is_(True))
    elif status.lower() == 'blocked':
        query = query.filter(Doctor.is_active.is_(False))

    doctors = query.order_by(User.full_name.asc()).paginate(page=page, per_page=per_page, error_out=False)
    departments = Department.query.all()

    # Feature 2: today's load per doctor (booked / capacity)
    today_str = date.today()
    today_loads = {}
    for d in doctors.items:
        booked_today = Appointment.query.filter(
            Appointment.doctor_id == d.id,
            Appointment.status != 'Cancelled',
            db.func.date(Appointment.appointment_datetime) == today_str
        ).count()
        today_loads[d.id] = {'booked': booked_today, 'max': d.max_appointments_per_day or 20}

    return render_template('/admin/all_doctors.html', doctors=doctors, departments=departments,
                           total=doctors.total, page=page, pages=doctors.pages,
                           q=q, department=department, status=status, today_loads=today_loads)


@main.route('/admin/patients',methods=['GET'])
@login_required
def all_patients():
    if current_user.role.lower() != 'admin':
        flash("you are nod admin access denied , DANGER!")
        return redirect(url_for('main.home'))
    page = request.args.get('page', 1, type=int)
    per_page = 8
    q = request.args.get('q', '').strip()
    status = request.args.get('status', '').strip()

    query = Patient.query.join(User, Patient.user_id == User.id)
    if q:
        like = f'%{q}%'
        query = query.filter(db.or_(User.full_name.ilike(like), User.email.ilike(like)))
    if status.lower() == 'active':
        query = query.filter(Patient.is_active.is_(True))
    elif status.lower() == 'blocked':
        query = query.filter(Patient.is_active.is_(False))

    patients = query.order_by(User.full_name.asc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('/admin/all_patients.html', patients=patients,
                           total=patients.total, page=page, pages=patients.pages,
                           q=q, status=status)


@main.route('/admin/appointments',methods=['GET'])
@login_required
def all_appointments():
    if current_user.role.lower() != 'admin':
        flash("you are nod admin access denied , DANGER!")
        return redirect(url_for('main.home'))
    page = request.args.get('page', 1, type=int)
    per_page = 10
    q = request.args.get('q', '').strip()
    status = request.args.get('status', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    query = Appointment.query
    if q:
        like = f'%{q}%'
        query = query.filter(db.or_(Appointment.patient.has(User.full_name.ilike(like)),
                                    Appointment.doctor.has(User.full_name.ilike(like))))
    if status:
        query = query.filter(Appointment.status.ilike(f'%{status}%'))
    if date_from:
        try:
            query = query.filter(Appointment.appointment_datetime >= datetime.strptime(date_from, '%Y-%m-%d'))
        except ValueError:
            pass
    if date_to:
        try:
            query = query.filter(Appointment.appointment_datetime <= datetime.strptime(date_to, '%Y-%m-%d') + __import__('datetime').timedelta(days=1))
        except ValueError:
            pass

    all_appointment = query.order_by(Appointment.appointment_datetime.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('/admin/all_appointment.html', appointments=all_appointment,
                           total=all_appointment.total, page=page, pages=all_appointment.pages,
                           q=q, status=status, date_from=date_from, date_to=date_to)


@main.route('/admin/add_doctor', methods=['GET', 'POST'])
@login_required
# @admin_required
def add_doctor():
    if request.method == 'POST':
        if current_user.role.lower() != 'admin':
            flash('Access denied.', 'danger')
            return redirect(url_for('main.home'))

        full_name = (request.form.get('full_name') or '').strip()
        email = (request.form.get('email') or '').strip().lower()
        specialization = (request.form.get('specialization') or '').strip()

        # Only name, email and department are required to create the account
        if not full_name or not email or not specialization:
            flash('Please provide the doctor name, email and department.', 'danger')
            return redirect(url_for('main.add_doctor'))
        if '@' not in email or '.' not in email:
            flash('Please enter a valid email address.', 'danger')
            return redirect(url_for('main.add_doctor'))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please use a different email.', 'warning')
            return redirect(url_for('main.add_doctor'))

        # Auto-generate a temporary password
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits
        generated_password = 'Doc@' + ''.join(secrets.choice(alphabet) for _ in range(8))

        # Get or create the department from the specialization entered
        dep = Department.query.filter_by(name=specialization).first()
        if not dep:
            dep = Department(name=specialization, description=f'Department of {specialization}')
            db.session.add(dep)
            db.session.commit()
        dep_id = dep.id

        new_doctor = User(
            full_name=full_name,
            email=email,
            password=generate_password_hash(generated_password),
            phone_number='0000000000',   # doctor completes this in Profile Settings
            age=0,                       # doctor completes this in Profile Settings
            gender='Other',              # doctor completes this in Profile Settings
            role='doctor'
        )
        doctor_data = Doctor(
            department_id=dep_id,
            qualification='Not specified',  # doctor completes this in Profile Settings
            specialization=specialization,
            experience_years=0,             # doctor completes this in Profile Settings
            bio='',
            user=new_doctor
        )

        db.session.add(new_doctor)
        db.session.add(doctor_data)
        db.session.commit()

        # Send credentials to the doctor's email (falls back to console log if SMTP not configured)
        try:
            from .emailer import send_doctor_credentials_email
            send_doctor_credentials_email(
                doctor_name=full_name,
                email=email,
                generated_password=generated_password,
                login_url=request.host_url
            )
        except Exception as e:
            print('Credentials email error:', e)

        flash('Doctor added successfully!', 'success')
        flash(f'Login credentials have been sent to {email}. '
              f'Temporary password: {generated_password} (doctor can change it after first login).', 'info')
        return redirect(url_for('main.admin_dashboard'))
    return render_template('admin/add_doctor.html')


#

@main.route('/admin/doctor/<int:doctor_id>', methods=['GET'])
@login_required
def view_doctor(doctor_id):
    if current_user.role.lower() != 'admin':
        flash("access denied you are not admin , danger")
        return redirect(url_for('main.home'))
    doctor = Doctor.query.get_or_404(doctor_id)
    return render_template('admin/doctor_profile.html', doctor=doctor)

@main.route('/admin/delete_doctor/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
def delete_doctor(doctor_id):
    if current_user.role.lower() != 'admin':
        flash("access denied you are not admin , danger")
        return redirect(url_for('main.home'))
    doctor = Doctor.query.get_or_404(doctor_id)
    user = User.query.get_or_404(doctor.user_id)

    if user.is_deleted or not doctor.is_active and user.is_deleted:
        # Already soft-deleted
        if request.method == 'POST':
            flash('This doctor is already deactivated.', 'info')
            return redirect(url_for('main.all_doctors'))
        return redirect(url_for('main.view_doctor', doctor_id=doctor.id))

    now = datetime.now()
    upcoming = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.appointment_datetime >= now,
        db.func.lower(Appointment.status) == 'booked'
    ).all()

    if request.method == 'POST':
        perform_doctor_deactivation(doctor, user, upcoming, request)
        flash('Doctor deactivated successfully. Patient data preserved; '
              'appointments reassigned or flagged as needing attention.', 'success')
        return redirect(url_for('main.all_doctors'))

    # GET -> show confirmation summary
    reassignable = []
    needs_attention = []
    for appt in upcoming:
        replacement = find_replacement_doctor(doctor, appt)
        if replacement:
            reassignable.append((appt, replacement))
        else:
            needs_attention.append(appt)

    return render_template('admin/confirm_delete_doctor.html', doctor=doctor,
                           upcoming=upcoming, reassignable=reassignable,
                           needs_attention=needs_attention)


def find_replacement_doctor(doctor, appointment):
    """Find an active doctor in the same department who can take over this appointment."""
    if not appointment.appointment_datetime:
        return None
    candidates = Doctor.query.filter(
        Doctor.department_id == doctor.department_id,
        Doctor.id != doctor.id,
        Doctor.is_active.is_(True)
    ).all()
    # Exclude doctors whose user account is soft-deleted
    candidates = [d for d in candidates if d.user and not d.user.is_deleted]
    for candidate in candidates:
        # 1. Capacity check for that date
        day_booked = Appointment.query.filter(
            Appointment.doctor_id == candidate.id,
            Appointment.status != 'Cancelled',
            db.func.date(Appointment.appointment_datetime) == appointment.appointment_datetime.date()
        ).count()
        if day_booked >= (candidate.max_appointments_per_day or 20):
            continue
        # 2. Availability check for that day-of-week / time
        day_name = appointment.appointment_datetime.strftime('%A')
        avail = DoctorAvailability.query.filter_by(
            doctor_id=candidate.id, day_of_week=day_name
        ).first()
        if not avail or not avail.is_available:
            continue
        appt_time = appointment.appointment_datetime.time()
        in_morning = avail.start_time_before_lunch and avail.end_time_before_lunch and \
            avail.start_time_before_lunch <= appt_time <= avail.end_time_before_lunch
        in_evening = avail.start_time_after_lunch and avail.end_time_after_lunch and \
            avail.start_time_after_lunch <= appt_time <= avail.end_time_after_lunch
        if in_morning or in_evening:
            return candidate
    return None


def perform_doctor_deactivation(doctor, user, upcoming, request=None):
    """Soft-delete the doctor and handle their upcoming appointments."""
    from datetime import datetime as _dt

    reassigned_count = 0
    needs_attention_count = 0

    for appt in upcoming:
        replacement = find_replacement_doctor(doctor, appt)
        patient = appt.patient
        old_name = f"Dr. {doctor.user.full_name}"
        dt_str = appt.appointment_datetime.strftime('%Y-%m-%d %H:%M')

        if replacement:
            appt.reassigned_from_doctor_id = doctor.id
            appt.needs_reassignment = False
            appt.reassigned_at = _dt.utcnow()
            appt.doctor_id = replacement.id
            reassigned_count += 1
            if patient:
                create_notification(
                    patient.user_id,
                    'Appointment reassigned',
                    f'Your appointment with {old_name} on {dt_str} has been reassigned to Dr. {replacement.user.full_name} at the same time.',
                    url_for('main.view_appointment', appointment_id=appt.id))
                try:
                    from .emailer import send_appointment_email
                    send_appointment_email(appt, 'confirmed')
                except Exception as e:
                    print('Reassign email error:', e)
        else:
            appt.needs_reassignment = True
            needs_attention_count += 1
            if patient:
                create_notification(
                    patient.user_id,
                    'Appointment needs rescheduling',
                    f'Your appointment with {old_name} on {dt_str} needs to be rescheduled. Our team will contact you shortly.',
                    url_for('main.view_appointment', appointment_id=appt.id))

    # Soft-delete the doctor account
    doctor.is_active = False
    user.is_deleted = True
    db.session.commit()
    return reassigned_count, needs_attention_count


def find_next_available_day(doctor, capacity_map, max_per_day=20):
    """Find the next date (from today) where the doctor has capacity and an availability slot."""
    from datetime import timedelta as _td, date as _date
    today = _date.today()
    week_days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    for offset in range(1, 61):  # look ahead 60 days
        d = today + _td(days=offset)
        dk = d.strftime('%Y-%m-%d')
        booked = capacity_map.get(dk, 0)
        if booked >= max_per_day:
            continue
        day_name = d.strftime('%A')
        avail = DoctorAvailability.query.filter_by(
            doctor_id=doctor.id, day_of_week=day_name
        ).first()
        if avail and avail.is_available:
            return dk
    return None


@main.route('/admin/appointment/<int:appointment_id>/reassign', methods=['POST'])
@login_required
def admin_reassign_appointment(appointment_id):
    if current_user.role.lower() != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.home'))
    appt = Appointment.query.get_or_404(appointment_id)
    new_doctor_id = request.form.get('doctor_id')
    if not new_doctor_id:
        flash('Please select a doctor to reassign to.', 'warning')
        return redirect(request.referrer or url_for('main.admin_dashboard'))

    new_doctor = Doctor.query.get(int(new_doctor_id))
    if not new_doctor or not new_doctor.is_active or new_doctor.user.is_deleted:
        flash('Selected doctor is not available.', 'danger')
        return redirect(request.referrer or url_for('main.admin_dashboard'))

    old_name = f"Dr. {appt.doctor.user.full_name}"
    appt.reassigned_from_doctor_id = appt.doctor_id
    appt.needs_reassignment = False
    appt.reassigned_at = datetime.utcnow()
    appt.doctor_id = new_doctor.id

    patient = appt.patient
    if patient:
        create_notification(patient.user_id, 'Appointment reassigned',
                            f'Your appointment has been reassigned to Dr. {new_doctor.user.full_name} on {appt.appointment_datetime.strftime("%Y-%m-%d %H:%M")}.',
                            url_for('main.view_appointment', appointment_id=appt.id))

    db.session.commit()
    flash(f'Appointment #{appt.id} reassigned to Dr. {new_doctor.user.full_name}.', 'success')
    return redirect(request.referrer or url_for('main.admin_dashboard'))

@main.route('/admin/block_doctor/<int:doctor_id>', methods=['POST','GET'])
@login_required
def block_doctor(doctor_id):
    if current_user.role.lower() != 'admin':
        flash("access denied you are not admin , danger")
        return redirect(url_for('main.home'))
    doctor = Doctor.query.get_or_404(doctor_id)
    user = User.query.get_or_404(doctor.user_id)
    doctor.is_active = False
    db.session.commit()
    return redirect(url_for('main.view_doctor', doctor_id=doctor.id))

@main.route('/admin/unblock_doctor/<int:doctor_id>', methods=['POST','GET'])
@login_required
def unblock_doctor(doctor_id):
    if current_user.role.lower() != 'admin':
        flash("access denied you are not admin , danger")
        return redirect(url_for('main.home'))
    doctor = Doctor.query.get_or_404(doctor_id)
    user = User.query.get_or_404(doctor.user_id)
    doctor.is_active = True
    db.session.commit()
    
    return redirect(url_for('main.view_doctor', doctor_id=doctor.id))

@main.route('/admin/edit_doctor/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
def edit_doctor(doctor_id):
    if current_user.role.lower() != 'admin':
        flash("access denied you are not admin , danger")
        return redirect(url_for('main.home'))
    doctor = Doctor.query.get_or_404(doctor_id)
    if request.method == 'POST':
        doctor.user.full_name = request.form.get('full_name')
        doctor.user.phone_number = request.form.get('phone_number')
        doctor.specialization = request.form.get('specialization')
        doctor.experience_years = request.form.get('experience_years')
        cap_val = request.form.get('max_appointments_per_day')
        if cap_val and str(cap_val).isdigit():
            doctor.max_appointments_per_day = int(cap_val)
        db.session.commit()
        flash('Doctor details updated successfully!', 'success')
        return redirect(url_for('main.all_doctors'))
    return render_template('admin/edit_doctor.html', doctor=doctor)



@main.route('/admin/patient/<int:patient_id>', methods=['GET'])
@login_required
def view_patient(patient_id):
    if current_user.role.lower() != 'admin':
        flash("access denied you are not admin , danger")
        return redirect(url_for('main.home'))
    patient = Patient.query.get_or_404(patient_id)
    return render_template('admin/patient_profile.html', patient=patient)

@main.route('/admin/delete_patient/<int:patient_id>', methods=['POST','GET'])
@login_required
def delete_patient(patient_id):
    if current_user.role.lower() != 'admin':
        flash("access denied you are not admin , danger")
        return redirect(url_for('main.home'))
    patient = Patient.query.get_or_404(patient_id)
    user = User.query.get_or_404(patient.user_id)
    appointments = Appointment.query.filter_by(patient_id=patient.id).all()
    for appointment in appointments:
        db.session.delete(appointment)
    db.session.delete(patient)
    db.session.delete(user)
    db.session.commit()
    
    return redirect(url_for('main.all_patients'))


@main.route('/admin/block_patient/<int:patient_id>', methods=['POST','GET'])
@login_required
def block_patient(patient_id):
    if current_user.role.lower() != 'admin':
        flash("access denied you are not admin , danger")
        return redirect(url_for('main.home'))
    patient = Patient.query.get_or_404(patient_id)
    user = User.query.get_or_404(patient.user_id)
    patient.is_active = False
    db.session.commit()
    
    return redirect(url_for('main.view_patient' , patient_id=patient.id))

@main.route('/admin/unblock_patient/<int:patient_id>', methods=['POST','GET'])
@login_required
def unblock_patient(patient_id):
    if current_user.role.lower() != 'admin':
        flash("access denied you are not admin , danger")
        return redirect(url_for('main.home'))
    patient = Patient.query.get_or_404(patient_id)
    user = User.query.get_or_404(patient.user_id)
    patient.is_active = True
    db.session.commit()
    
    return redirect(url_for('main.view_patient' , patient_id=patient.id))

@main.route('/admin/edit_patient/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def edit_patient(patient_id):
    if current_user.role.lower() != 'admin':
        flash("access denied you are not admin , danger")
        return redirect(url_for('main.home'))
    patient = Patient.query.get_or_404(patient_id)
    if request.method == 'POST':
        patient.user.full_name = request.form.get('full_name')
        patient.user.phone_number = request.form.get('phone_number')
        patient.user.age = request.form.get('age')
        db.session.commit()
        flash('Patient details updated successfully!', 'success')
        return redirect(url_for('main.all_patients'))
    return render_template('admin/edit_patient.html', patient=patient)


@main.route('/admin/patient/view_report/<int:appointment_id>')
@login_required
def admin_view_report(appointment_id):
    if current_user.role.lower() != 'admin':
        flash("Accesss denied you are not admin, Danger!")
        return redirect(url_for('main.home'))
    appointment = Appointment.query.get_or_404(appointment_id)
    return render_template('admin/patient_report.html' , appointment=appointment)
    




#========== Routes Manage by Doctor =============



@main.route('/doctor/provide/weekly_availability' , methods=['POST' , 'GET'])
@login_required
def set_availability():
    if current_user.role.lower() != 'doctor':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.home'))
    doctor_id = current_user.doctor.id

    # Apne fixed time slots ko Python 'time' objects me define karein
    # Yeh HTML ke 'slot1' aur 'slot2' se match honge
    MORNING_START = time(8, 0, 0)  # 08:00 AM
    MORNING_END = time(12, 0, 0) # 12:00 PM
    EVENING_START = time(16, 0, 0) # 04:00 PM
    EVENING_END = time(21, 0, 0) # 09:00 PM

    if request.method == 'POST':
        try:
            days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            
            for day in days:
                # Check karein 'Not Available' switch ON hai ya nahi
                is_off = f'{day}-off' in request.form
                
                # Default values ko None set karein
                start_morning = None
                end_morning = None
                start_evening = None
                end_evening = None

                # Agar doctor OFF nahi hai, to slots check  
                if not is_off:
                    available_slots = request.form.getlist(day)     # eg. ['slot1', 'slot2']
                    
                    if 'slot1' in available_slots:
                        start_morning = MORNING_START
                        end_morning = MORNING_END
                    
                    if 'slot2' in available_slots:
                        start_evening = EVENING_START
                        end_evening = EVENING_END
                
              
                
                # check Dr ki availability pehle se DB me hai ya nahi
                avail = DoctorAvailability.query.filter_by(
                    doctor_id=doctor_id, 
                    day_of_week=day.capitalize()
                ).first()
                
                if avail:
                    # Agar hai, toh update karein
                    avail.is_available = not is_off # Agar off hai, toh is_available = False
                    avail.start_time_before_lunch = start_morning
                    avail.end_time_before_lunch = end_morning
                    avail.start_time_after_lunch = start_evening
                    avail.end_time_after_lunch = end_evening
                else:
                    # Agar nahi hai, toh nayi entry banayein
                    avail = DoctorAvailability(
                        doctor_id=doctor_id,
                        day_of_week=day.capitalize(),
                        is_available = not is_off,
                        start_time_before_lunch = start_morning,
                        end_time_before_lunch = end_morning,
                        start_time_after_lunch = start_evening,
                        end_time_after_lunch = end_evening
                    )
                    db.session.add(avail)

            db.session.commit()
            flash('Availability updated successfully!', 'success')
            
        except Exception as e:
            db.session.rollback() 
            flash(f'Error updating availability: {e}', 'danger')

        return redirect(url_for('main.set_availability'))

    # GET request ke liye, pehle se maujood availability fetch kiya
    current_availability_db = DoctorAvailability.query.filter_by(doctor_id=doctor_id).all()
    
    # Ise ek simple dictionary me badal dein taaki template me bheja ja sake
    # Key: 'monday', Value: poora 'avail' object
    availability_data = {}
    for item in current_availability_db:
        day_name = item.day_of_week.lower() 
        availability_data[day_name] = item # Poora object save kar rahe hain

    return render_template('doctor/provide_availability.html', availability_data=availability_data)

    



@main.route('/doctor/appoitment',methods=['GET','POST'])
@login_required
def manage_appointment():
    if current_user.role.lower() != 'doctor':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.home'))
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    appointments = Appointment.query.filter_by(doctor_id=doctor.id).all()
    patients = Patient.query.filter_by(user_id=current_user.id).all()
    upcomming_count = 0
    done_count = 0
    for appointment in appointments:
        if appointment.status.lower() == 'booked':
            upcomming_count = upcomming_count+1
        else:
            done_count = done_count+1
    return render_template('doctor/manage_appointment.html', appointments=appointments , upcomming_count=upcomming_count ,done_count=done_count)




@main.route("/doctor/history/save/<int:appointment_id>", methods=["POST"])
@login_required
def save_patient_history(appointment_id):

    appointment = Appointment.query.get_or_404(appointment_id)

    # Authorization: only the assigned doctor or admin may edit
    if not (current_user.role.lower() == 'admin' or
            (current_user.role.lower() == 'doctor' and hasattr(current_user, 'doctor') and appointment.doctor_id == current_user.doctor.id)):
        flash("Unauthorized access!", "danger")
        return redirect(url_for('main.home'))

    history = appointment.history 

    if not history:
        history = PatientHistory(appointment_id=appointment.id)
        db.session.add(history)

    history.visit_type = request.form.get("visit_type")
    history.tests_done = request.form.get("tests_done")
    history.diagnosis = request.form.get("diagnosis")
    history.prescription_notes = request.form.get("prescription")

    # remove old meds if updating
    PrescribedMedicine.query.filter_by(history_id=history.id).delete()

    # new medicines list
    meds = request.form.getlist("medicine_name")
    doses = request.form.getlist("dosage")

    for med_name, dose in zip(meds, doses):
        if med_name and med_name.strip():
            new_med = PrescribedMedicine(history_id=history.id,
                                         medicine_name=med_name.strip(),
                                         dosage=(dose or '').strip())
            db.session.add(new_med)

    # Medical report / lab file uploads
    if 'report_file' in request.files:
        files = request.files.getlist('report_file')
        for f in files:
            if f and f.filename:
                allowed = current_app.config['ALLOWED_UPLOAD_EXTENSIONS']
                ext = f.filename.rsplit('.', 1)[-1].lower() if '.' in f.filename else ''
                if ext not in allowed:
                    flash(f"File '{f.filename}' has an invalid format.", "danger")
                    continue
                stored = save_upload(f, subfolder='uploads/reports', allowed_ext=allowed, max_bytes=10*1024*1024)
                if stored:
                    report = ReportFile(
                        appointment_id=appointment.id,
                        filename=stored,
                        original_name=f.filename,
                        file_type=ext,
                        uploaded_by=current_user.id
                    )
                    db.session.add(report)

    db.session.commit()
    flash("History Updated Successfully ✔", "success")
    return redirect(request.referrer or url_for('main.doctor_dashboard'))


@main.route('/report_file/delete/<int:file_id>', methods=['POST'])
@login_required
def delete_report_file(file_id):
    report = ReportFile.query.get_or_404(file_id)
    appointment = report.appointment
    is_admin = current_user.role.lower() == 'admin'
    is_own_doctor = current_user.role.lower() == 'doctor' and hasattr(current_user, 'doctor') and appointment.doctor_id == current_user.doctor.id
    if not (is_admin or is_own_doctor):
        flash("Unauthorized access!", "danger")
        return redirect(url_for('main.home'))
    try:
        path = os.path.join(current_app.root_path, 'static', 'uploads', 'reports', report.filename)
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
    db.session.delete(report)
    db.session.commit()
    flash("File deleted.", "success")
    return redirect(request.referrer)





# VIEW REPORT ROUTE
# ==========================
@main.route('/report/pdf/<int:appointment_id>')
@login_required
def download_report_pdf(appointment_id):
    """Generate and download a styled PDF prescription with hospital letterhead."""
    from fpdf import FPDF
    from io import BytesIO

    appointment = Appointment.query.get_or_404(appointment_id)

    # Authorization
    role = current_user.role.lower()
    is_admin = role == 'admin'
    is_own_doctor = role == 'doctor' and hasattr(current_user, 'doctor') and appointment.doctor_id == current_user.doctor.id
    is_own_patient = role == 'patient' and hasattr(current_user, 'patient') and appointment.patient_id == current_user.patient.id
    if not (is_admin or is_own_doctor or is_own_patient):
        flash("Unauthorized access!", "danger")
        return redirect(url_for('main.home'))

    history = appointment.history
    doctor = appointment.doctor
    patient = appointment.patient

    class Pdf(FPDF):
        def header(self):
            self.set_fill_color(26, 92, 143)
            self.rect(0, 0, 210, 28, 'F')
            self.set_text_color(255, 255, 255)
            self.set_font('Helvetica', 'B', 18)
            self.cell(0, 12, 'HMS Portal Hospital', ln=True, align='C')
            self.set_font('Helvetica', '', 9)
            self.cell(0, 6, 'Your Health, Our Priority  |  Phone: +91-612-2370419  |  Email: info@hmsp.com', ln=True, align='C')
            self.set_text_color(30, 30, 30)
            self.ln(12)

        def footer(self):
            self.set_y(-18)
            self.set_draw_color(200, 200, 200)
            self.line(10, self.get_y(), 200, self.get_y())
            self.set_font('Helvetica', 'I', 8)
            self.set_text_color(130, 130, 130)
            self.cell(0, 8, 'This is a computer generated prescription. Signature: ____________________', align='C')

    pdf = Pdf()
    pdf.add_page()
    pdf.set_left_margin(12)
    pdf.set_right_margin(12)

    # Prescription header
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(26, 92, 143)
    pdf.cell(0, 8, 'MEDICAL PRESCRIPTION', ln=True)
    pdf.set_draw_color(0, 201, 167)
    pdf.line(12, pdf.get_y(), 198, pdf.get_y())
    pdf.ln(6)

    # Doctor / patient info
    pdf.set_text_color(30, 30, 30)
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(0, 7, f"Doctor: Dr. {doctor.user.full_name}  ({doctor.specialization})", ln=True)
    pdf.cell(0, 7, f"Qualification: {doctor.qualification}  |  Experience: {doctor.experience_years} years", ln=True)
    pdf.cell(0, 7, f"Patient: {patient.user.full_name}   Age: {patient.user.age}   Gender: {patient.user.gender}", ln=True)
    dt = appointment.appointment_datetime
    pdf.cell(0, 7, f"Date: {dt.strftime('%B %d, %Y  %I:%M %p') if dt else 'N/A'}", ln=True)
    pdf.ln(4)

    pdf.set_draw_color(200, 200, 200)
    pdf.line(12, pdf.get_y(), 198, pdf.get_y())
    pdf.ln(3)

    if history:
        if history.diagnosis:
            pdf.set_font('Helvetica', 'B', 11)
            pdf.cell(0, 7, 'Diagnosis:', ln=True)
            pdf.set_font('Helvetica', '', 11)
            pdf.multi_cell(0, 6, str(history.diagnosis))
            pdf.ln(2)

        if history.tests_done:
            pdf.set_font('Helvetica', 'B', 11)
            pdf.cell(0, 7, 'Tests Done:', ln=True)
            pdf.set_font('Helvetica', '', 11)
            pdf.multi_cell(0, 6, str(history.tests_done))
            pdf.ln(2)

        pdf.set_font('Helvetica', 'B', 11)
        pdf.cell(0, 7, 'Prescribed Medicines:', ln=True)
        pdf.ln(1)
        meds = history.medicines if history.medicines else []
        if meds:
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_fill_color(240, 247, 250)
            pdf.cell(90, 8, 'Medicine Name', border=1, fill=True)
            pdf.cell(80, 8, 'Dosage', border=1, fill=True)
            pdf.ln()
            pdf.set_font('Helvetica', '', 10)
            for m in meds:
                pdf.cell(90, 8, str(m.medicine_name or ''), border=1)
                pdf.cell(80, 8, str(m.dosage or ''), border=1)
                pdf.ln()
        else:
            pdf.set_font('Helvetica', 'I', 10)
            pdf.cell(0, 7, 'No medicines prescribed.')
            pdf.ln()

        pdf.ln(3)
        if history.prescription_notes:
            pdf.set_font('Helvetica', 'B', 11)
            pdf.cell(0, 7, 'Notes:', ln=True)
            pdf.set_font('Helvetica', '', 11)
            pdf.multi_cell(0, 6, str(history.prescription_notes))
    else:
        pdf.set_font('Helvetica', 'I', 11)
        pdf.cell(0, 8, 'No medical report available for this appointment.')

    pdf.ln(6)
    pdf.set_font('Helvetica', 'I', 9)
    pdf.set_text_color(130, 130, 130)
    pdf.cell(0, 6, 'Generated by HMS Portal - secure digital prescriptions')

    buf = BytesIO()
    pdf.output(buf)
    buf.seek(0)
    from flask import Response
    filename = f"prescription_{appointment.id}.pdf"
    return Response(
        buf,
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


@main.route('/doctor/view_report/<int:appointment_id>')
@login_required
def view_patient_report(appointment_id):
    if current_user.role.lower() != 'doctor':
        flash("Access denied ,Danger!")
        return redirect(url_for('main.home'))
    # Fetch appointment by ID
    appointment = Appointment.query.get_or_404(appointment_id)

    # Access restriction: doctor can view only his own appointment reports
    if appointment.doctor_id != current_user.doctor.id:
        flash("Unauthorized Access!", "danger")
        return redirect(url_for('main.doctor_dashboard'))

    return render_template("doctor/patient_report.html", appointment=appointment)

@main.route('/doctor/assigned_patients' , methods=['GET'])
@login_required
def assigned_patients():
    if current_user.role.lower() != 'doctor':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.home'))
    doctor = Doctor.query.get(current_user.doctor.id)
    appointments = Appointment.query.filter_by(doctor_id=doctor.id).all()
    patient_count = len(appointments)
    return render_template('doctor/assigned_patient.html', appointments=appointments , patient_count=patient_count)


#=========================================== Routes Manage by Patient ===============================

# ===================== Chat Routes =====================

@main.route('/chat/<int:appointment_id>', methods=['GET'])
@login_required
def chat_room(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    role = current_user.role.lower()
    is_admin = role == 'admin'
    is_own_doctor = role == 'doctor' and hasattr(current_user, 'doctor') and appointment.doctor_id == current_user.doctor.id
    is_own_patient = role == 'patient' and hasattr(current_user, 'patient') and appointment.patient_id == current_user.patient.id
    if not (is_admin or is_own_doctor or is_own_patient):
        flash("Unauthorized access!", "danger")
        return redirect(url_for('main.home'))
    messages = ChatMessage.query.filter_by(appointment_id=appointment_id).order_by(ChatMessage.created_at.asc()).all()
    return render_template('chat/room.html', appointment=appointment, messages=messages)


@main.route('/chat/<int:appointment_id>/upload', methods=['POST'])
@login_required
def chat_upload(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    role = current_user.role.lower()
    is_admin = role == 'admin'
    is_own_doctor = role == 'doctor' and hasattr(current_user, 'doctor') and appointment.doctor_id == current_user.doctor.id
    is_own_patient = role == 'patient' and hasattr(current_user, 'patient') and appointment.patient_id == current_user.patient.id
    if not (is_admin or is_own_doctor or is_own_patient):
        return jsonify({'error': 'Unauthorized'}), 403

    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    stored = save_upload(file, subfolder='uploads/chat', allowed_ext=current_app.config['ALLOWED_UPLOAD_EXTENSIONS'], max_bytes=10*1024*1024)
    if not stored:
        return jsonify({'error': 'Invalid file type or file too large (max 10 MB).'}), 400

    return jsonify({'url': url_for('static', filename=f'uploads/chat/{stored}'), 'name': file.filename})


@main.route('/uploads/<path:filename>')
@login_required
def serve_upload(filename):
    return send_from_directory(os.path.join(current_app.root_path, 'static', 'uploads'), filename)


@main.route('/chat/<int:appointment_id>/messages', methods=['GET'])
@login_required
def chat_messages(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    role = current_user.role.lower()
    is_admin = role == 'admin'
    is_own_doctor = role == 'doctor' and hasattr(current_user, 'doctor') and appointment.doctor_id == current_user.doctor.id
    is_own_patient = role == 'patient' and hasattr(current_user, 'patient') and appointment.patient_id == current_user.patient.id
    if not (is_admin or is_own_doctor or is_own_patient):
        return jsonify({'error': 'Unauthorized'}), 403
    messages = ChatMessage.query.filter_by(appointment_id=appointment_id).order_by(ChatMessage.created_at.asc()).all()
    data = [{
        'id': m.id,
        'sender_id': m.sender_id,
        'sender_name': m.sender.full_name,
        'message': m.message,
        'file_url': m.file_url,
        'file_name': m.file_name,
        'is_read': m.is_read,
        'created_at': m.created_at.strftime('%Y-%m-%d %H:%M:%S') if m.created_at else ''
    } for m in messages]
    return jsonify(data)


# ===================== Video Consultation Routes =====================

@main.route('/video/<int:appointment_id>', methods=['GET'])
@login_required
def video_room(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    role = current_user.role.lower()
    is_admin = role == 'admin'
    is_own_doctor = role == 'doctor' and hasattr(current_user, 'doctor') and appointment.doctor_id == current_user.doctor.id
    is_own_patient = role == 'patient' and hasattr(current_user, 'patient') and appointment.patient_id == current_user.patient.id
    if not (is_admin or is_own_doctor or is_own_patient):
        flash("Unauthorized access!", "danger")
        return redirect(url_for('main.home'))
    # Get or create a video room
    video = VideoRoom.query.filter_by(appointment_id=appointment_id).first()
    if not video:
        room_name = f"hms-{uuid.uuid4().hex[:12]}"
        video = VideoRoom(appointment_id=appointment_id, room_name=room_name, status='pending')
        db.session.add(video)
        db.session.commit()
    return render_template('chat/video.html', appointment=appointment, video=video)


@main.route('/video/<int:appointment_id>/start', methods=['POST'])
@login_required
def start_video_call(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    role = current_user.role.lower()
    is_own_doctor = role == 'doctor' and hasattr(current_user, 'doctor') and appointment.doctor_id == current_user.doctor.id
    is_own_patient = role == 'patient' and hasattr(current_user, 'patient') and appointment.patient_id == current_user.patient.id
    if not (is_own_doctor or is_own_patient):
        return jsonify({'error': 'Unauthorized'}), 403
    video = VideoRoom.query.filter_by(appointment_id=appointment_id).first()
    if not video:
        video = VideoRoom(appointment_id=appointment_id, room_name=f"hms-{uuid.uuid4().hex[:12]}", status='pending')
        db.session.add(video)
        db.session.flush()
    video.status = 'active'
    video.started_at = datetime.utcnow()
    db.session.commit()
    # Notify other party
    notify_other_party(appointment, 'Video call started',
                       f'{current_user.full_name} has started a video call.',
                       url_for('main.video_room', appointment_id=appointment_id))
    return jsonify({'status': 'active', 'room_name': video.room_name})


@main.route('/video/<int:appointment_id>/end', methods=['POST'])
@login_required
def end_video_call(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    role = current_user.role.lower()
    is_own_doctor = role == 'doctor' and hasattr(current_user, 'doctor') and appointment.doctor_id == current_user.doctor.id
    is_own_patient = role == 'patient' and hasattr(current_user, 'patient') and appointment.patient_id == current_user.patient.id
    if not (is_own_doctor or is_own_patient):
        return jsonify({'error': 'Unauthorized'}), 403
    video = VideoRoom.query.filter_by(appointment_id=appointment_id).first()
    if video:
        video.status = 'ended'
        video.ended_at = datetime.utcnow()
        db.session.commit()
    return jsonify({'status': 'ended'})


# ===================== Ratings & Reviews =====================

@main.route('/appointment/<int:appointment_id>/rate', methods=['POST'])
@login_required
def rate_doctor(appointment_id):
    """Allow a patient to rate a doctor after a completed appointment."""
    if current_user.role.lower() != 'patient':
        flash("Only patients can rate doctors.", "danger")
        return redirect(url_for('main.home'))

    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.patient_id != current_user.patient.id:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('main.home'))
    if appointment.status.lower() != 'completed':
        flash("You can only rate a doctor after the appointment is completed.", "warning")
        return redirect(url_for('main.booked_appointment_list'))

    try:
        rating_val = int(request.form.get('rating', 0))
    except (TypeError, ValueError):
        rating_val = 0
    review = (request.form.get('review') or '').strip()

    if rating_val < 1 or rating_val > 5:
        flash("Please select a rating between 1 and 5 stars.", "warning")
        return redirect(url_for('main.view_report', appointment_id=appointment.id))

    existing = DoctorRating.query.filter_by(appointment_id=appointment.id).first()
    if existing:
        existing.rating = rating_val
        existing.review = review
        db.session.commit()
        flash("Your rating has been updated. Thank you!", "success")
    else:
        rating = DoctorRating(
            doctor_id=appointment.doctor_id,
            patient_id=appointment.patient_id,
            appointment_id=appointment.id,
            rating=rating_val,
            review=review
        )
        db.session.add(rating)
        db.session.commit()
        flash("Thank you for rating the doctor!", "success")

    return redirect(url_for('main.view_report', appointment_id=appointment.id))


@main.route('/doctor/<int:doctor_id>/reviews')
@login_required
def doctor_reviews(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    reviews = DoctorRating.query.filter_by(doctor_id=doctor.id).order_by(DoctorRating.created_at.desc()).all()
    return render_template('patient/doctor_reviews.html', doctor=doctor, reviews=reviews)


# ===================== Medical History Timeline =====================

@main.route('/patient/medical_history')
@login_required
def medical_history():
    if current_user.role.lower() != 'patient':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.home'))
    appointments = Appointment.query.filter_by(patient_id=current_user.patient.id) \
        .filter(db.func.lower(Appointment.status) == 'completed') \
        .order_by(Appointment.appointment_datetime.desc()).all()
    return render_template('patient/medical_history.html', appointments=appointments)




@main.route('/notifications', methods=['GET'])
@login_required
def notification_list():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    notifs = Notification.query.filter_by(recipient_id=current_user.id)\
        .order_by(Notification.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    if request.args.get('format') == 'json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = [{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'link': n.link or '#',
            'is_read': n.is_read,
            'created_at': n.created_at.strftime('%Y-%m-%d %H:%M') if n.created_at else ''
        } for n in notifs.items]
        return jsonify({'notifications': data})

    return render_template('notifications/list.html', notifications=notifs)


@main.route('/notifications/unread_count', methods=['GET'])
@login_required
def notification_unread_count():
    count = Notification.query.filter_by(recipient_id=current_user.id, is_read=False).count()
    return jsonify({'unread_count': count})


@main.route('/notifications/mark_read/<int:notif_id>', methods=['POST'])
@login_required
def mark_notification_read(notif_id):
    notif = Notification.query.get_or_404(notif_id)
    if notif.recipient_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    notif.is_read = True
    db.session.commit()
    return jsonify({'status': 'ok'})


@main.route('/notifications/mark_all_read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    Notification.query.filter_by(recipient_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'status': 'ok'})



@main.route('/check_availability/<int:doctor_id>' , methods=['GET'])
@login_required
def check_availability(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    appointments = Appointment.query.filter_by(doctor_id=doctor.id).all()
    available_slots = DoctorAvailability.query.filter_by(doctor_id=doctor.id).all()
    booked_slots = appointments
    return render_template('patient/check_availability.html', available_slots=available_slots, booked_slots=booked_slots)


#=====view Doctor Profile and all doctors =======

@main.route('/doctor_profile/<int:doctor_id>' , methods=['GET'])
@login_required
def doctor_profile(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    return render_template('patient/doctor_profile.html', doctor=doctor)


@main.route('/doctor_list' , methods=['GET'])
@login_required
def doctor_list():
    if current_user.role.lower() != 'patient':
        flash("access denied , DANGER !")
        return redirect(url_for('main.home'))
    page = request.args.get('page', 1, type=int)
    per_page = 6
    q = request.args.get('q', '').strip()
    department = request.args.get('department', '').strip()
    specialization = request.args.get('specialization', '').strip()

    query = Doctor.query.join(User, Doctor.user_id == User.id).filter(User.is_deleted.is_(False), Doctor.is_active.is_(True))
    if q:
        like = f'%{q}%'
        query = query.filter(db.or_(User.full_name.ilike(like), Doctor.specialization.ilike(like)))
    if department:
        query = query.filter(Doctor.department_id == int(department))
    if specialization:
        query = query.filter(Doctor.specialization.ilike(f'%{specialization}%'))

    doctors = query.order_by(User.full_name.asc()).paginate(page=page, per_page=per_page, error_out=False)
    departments = Department.query.all()
    specializations = db.session.query(Doctor.specialization).distinct().all()
    specializations = [s[0] for s in specializations]

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = [{
            'id': d.id,
            'name': f"Dr. {d.user.full_name}",
            'specialization': d.specialization,
            'experience': d.experience_years,
            'avatar': url_for('static', filename='img/' + (d.user.profile_picture or 'default.png')),
            'profile_url': url_for('main.get_doctor_profile', doctor_id=d.id),
        } for d in doctors.items]
        pagination_html = render_template('partials/pagination.html', pages=doctors.pages, page=page, q=q,
                                          department=department, specialization=specialization)
        return jsonify({'doctors': data, 'pagination_html': pagination_html})

    return render_template('patient/all_doctors.html', doctors=doctors, departments=departments,
                           specializations=specializations, q=q, department=department,
                           specialization=specialization, page=page, pages=doctors.pages, total=doctors.total)




#== Patient Book Appointment and Medical Records ===
def format_time(t):
    if t:
        return t.strftime("%I:%M %p")
    return None


@main.route('/doctor_availability/for_patient/<int:doctor_id>', methods=['GET'])
@login_required
def doctor_availability(doctor_id):
   
    doctor = Doctor.query.get_or_404(doctor_id)
    if doctor.user.is_deleted or not doctor.is_active:
        flash('This doctor is no longer available. Please choose another doctor.', 'warning')
        return redirect(url_for('main.doctor_list'))

    # Fetch availability from DB
    availabilities = DoctorAvailability.query.filter_by(doctor_id=doctor.id).all()
    
    # Organize data by day so we can loop through Monday-Sunday easily
    week_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    schedule_data = {}

    # Initialize empty structure
    for day in week_days:
        schedule_data[day] = {
            'morning': None,
            'evening': None,
            'is_available': False
        }

    # Fill with DB data
    for slot in availabilities:
        day_name = slot.day_of_week.capitalize()
        if day_name in schedule_data:
            schedule_data[day_name]['is_available'] = slot.is_available
            
            if slot.is_available:
                # Format Morning Slot
                if slot.start_time_before_lunch and slot.end_time_before_lunch:
                    schedule_data[day_name]['morning'] = f"{(slot.start_time_before_lunch)} - {(slot.end_time_before_lunch)}"
                
                # Format Evening Slot
                if slot.start_time_after_lunch and slot.end_time_after_lunch:
                    schedule_data[day_name]['evening'] = f"{(slot.start_time_after_lunch)} - {(slot.end_time_after_lunch)}"

    # Build JSON for calendar picker
    slots_json = {}
    for day in week_days:
        slots = []
        sd = schedule_data[day]
        if sd['is_available']:
            if sd['morning']:
                slots.append(sd['morning'].split(' - ')[0].strip())
            if sd['evening']:
                slots.append(sd['evening'].split(' - ')[0].strip())
        slots_json[day] = slots

    booked_appointments = Appointment.query.filter_by(doctor_id=doctor.id).filter(Appointment.status != 'Cancelled').all()
    booked_json = [a.appointment_datetime.strftime('%Y-%m-%d %H:%M:%S') for a in booked_appointments if a.appointment_datetime]

    # ---- Feature 2: daily capacity ----
    max_per_day = doctor.max_appointments_per_day or 20
    capacity_map = {}
    for a in booked_appointments:
        if a.appointment_datetime:
            dk = a.appointment_datetime.strftime('%Y-%m-%d')
            capacity_map[dk] = capacity_map.get(dk, 0) + 1
    next_available = find_next_available_day(doctor, capacity_map, max_per_day)

    return render_template('auth/doct_availability.html', doctor=doctor, schedule=schedule_data, week_days=week_days,
                           slots_json=slots_json, booked_json=booked_json,
                           max_per_day=max_per_day, capacity_map=capacity_map, next_available=next_available)


@main.route('/book_appointment_slot', methods=['POST'])
@login_required
def book_appointment_slot():
    if current_user.role.lower() != 'patient':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.home'))
    
    try:
        doctor_id = request.form.get("doctor_id")
        slot_time = request.form.get("slot_time")      # example -> "08:00"
        appointment_date = request.form.get("appointment_date")  # yyyy-mm-dd format

        # Convert Date + Time to a combined datetime
        try:
            final_datetime = datetime.strptime(f"{appointment_date} {slot_time}", "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            flash("Invalid date or time selected.", "danger")
            return redirect(url_for('main.doctor_availability', doctor_id=doctor_id))

        if final_datetime <= datetime.now():
            flash("Please choose a future date and time.", "warning")
            return redirect(url_for('main.doctor_availability', doctor_id=doctor_id))

        # ---- Feature 2: enforce daily capacity ----
        doctor = Doctor.query.get(int(doctor_id))
        if not doctor or doctor.user.is_deleted or not doctor.is_active:
            flash('This doctor is no longer available. Please choose another doctor.', 'warning')
            return redirect(url_for('main.doctor_list'))

        max_per_day = doctor.max_appointments_per_day or 20
        day_booked = Appointment.query.filter(
            Appointment.doctor_id == doctor.id,
            Appointment.status != 'Cancelled',
            db.func.date(Appointment.appointment_datetime) == final_datetime.date()
        ).count()
        if day_booked >= max_per_day:
            # Build capacity map for this doctor to suggest the next available day
            all_booked = Appointment.query.filter_by(doctor_id=doctor.id).filter(Appointment.status != 'Cancelled').all()
            capacity_map = {}
            for a in all_booked:
                if a.appointment_datetime:
                    dk = a.appointment_datetime.strftime('%Y-%m-%d')
                    capacity_map[dk] = capacity_map.get(dk, 0) + 1
            nxt = find_next_available_day(doctor, capacity_map, max_per_day)
            if nxt:
                flash(f"Dr. {doctor.user.full_name} is fully booked on this day ({day_booked}/{max_per_day}). Next available day: {nxt}.", 'warning')
            else:
                flash(f"Dr. {doctor.user.full_name} is fully booked on this day. Please try another date.", 'warning')
            return redirect(url_for('main.doctor_availability', doctor_id=doctor_id))

        # check already booked? (Prevent duplicate)
        existing = Appointment.query.filter_by(
            doctor_id=doctor_id,
            patient_id=current_user.patient.id,
            appointment_datetime=final_datetime
        ).first()

        if existing:
            flash("You already booked this slot!", "warning")
            return redirect(url_for('main.doctor_availability', doctor_id=doctor_id))

        # Save in DB
        new_appt = Appointment(
            doctor_id = doctor_id,
            patient_id = current_user.patient.id,
            appointment_datetime = final_datetime,
            status = "booked"
        )
        db.session.add(new_appt)
        db.session.flush()

        # Notify the doctor
        if doctor:
            create_notification(doctor.user_id, "New appointment booked",
                                f"{current_user.full_name} booked an appointment on {final_datetime.strftime('%Y-%m-%d %H:%M')}.",
                                url_for('main.view_appointment', appointment_id=new_appt.id))

        # Email notification
        try:
            send_appointment_email(new_appt, 'booked')
        except Exception as e:
            print('Email error:', e)

        db.session.commit()

        flash("Appointment booked successfully!", "success")
        return redirect(url_for('main.booking_slip', appointment_id=new_appt.id))

    except Exception as e:
        db.session.rollback()
        print(e)
        flash("Something went wrong. Please try again.", "danger")
        doctor_id = request.form.get('doctor_id')
        if doctor_id:
            return redirect(url_for('main.doctor_availability', doctor_id=doctor_id))
        return redirect(url_for('main.patient_dashboard'))


# ===================== Booking Confirmation Slip (Feature 3) =====================

def _can_view_appointment(appointment):
    role = current_user.role.lower()
    if role == 'admin':
        return True
    if role == 'patient' and hasattr(current_user, 'patient') and appointment.patient_id == current_user.patient.id:
        return True
    if role == 'doctor' and hasattr(current_user, 'doctor') and appointment.doctor_id == current_user.doctor.id:
        return True
    return False


@main.route('/booking/<int:appointment_id>/slip', methods=['GET'])
@login_required
def booking_slip(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    if not _can_view_appointment(appointment):
        flash("Unauthorized access!", "danger")
        return redirect(url_for('main.home'))
    return render_template('patient/booking_slip.html', appointment=appointment)


@main.route('/booking/<int:appointment_id>/slip_pdf', methods=['GET'])
@login_required
def booking_slip_pdf(appointment_id):
    from fpdf import FPDF
    from io import BytesIO

    appointment = Appointment.query.get_or_404(appointment_id)
    if not _can_view_appointment(appointment):
        flash("Unauthorized access!", "danger")
        return redirect(url_for('main.home'))

    doctor = appointment.doctor
    patient = appointment.patient
    ref_no = f"HMS-{appointment.id:05d}"

    pdf = FPDF()
    pdf.add_page()
    pdf.set_left_margin(12)
    pdf.set_right_margin(12)

    # Header band
    pdf.set_fill_color(37, 99, 235)
    pdf.rect(0, 0, 210, 30, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Helvetica', 'B', 18)
    pdf.cell(0, 12, 'HMS Portal Hospital', ln=True, align='C')
    pdf.set_font('Helvetica', '', 9)
    pdf.cell(0, 6, 'Appointment Confirmation Slip  |  Ref: %s' % ref_no, ln=True, align='C')
    pdf.set_text_color(30, 30, 30)
    pdf.ln(12)

    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(37, 99, 235)
    pdf.cell(0, 8, 'APPOINTMENT CONFIRMATION', ln=True)
    pdf.set_draw_color(6, 182, 212)
    pdf.line(12, pdf.get_y(), 198, pdf.get_y())
    pdf.ln(6)

    pdf.set_text_color(30, 30, 30)
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(0, 7, 'Booking Reference: %s' % ref_no, ln=True)
    pdf.cell(0, 7, 'Status: Confirmed', ln=True)
    pdf.ln(3)

    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 7, 'Doctor', ln=True)
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(0, 7, 'Dr. %s  (%s)' % (doctor.user.full_name, doctor.specialization), ln=True)
    pdf.ln(2)

    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 7, 'Patient', ln=True)
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(0, 7, patient.user.full_name, ln=True)
    pdf.ln(2)

    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 7, 'Date & Time', ln=True)
    pdf.set_font('Helvetica', '', 11)
    dt = appointment.appointment_datetime
    pdf.cell(0, 7, dt.strftime('%A, %B %d, %Y at %I:%M %p') if dt else 'N/A', ln=True)
    pdf.ln(6)

    pdf.set_draw_color(200, 200, 200)
    pdf.line(12, pdf.get_y(), 198, pdf.get_y())
    pdf.ln(4)
    pdf.set_font('Helvetica', 'I', 9)
    pdf.set_text_color(130, 130, 130)
    pdf.cell(0, 6, 'Please arrive 10 minutes before your appointment time.', ln=True, align='C')
    pdf.cell(0, 6, 'Carry this slip or your booking reference number.', ln=True, align='C')

    buf = BytesIO()
    pdf.output(buf)
    buf.seek(0)
    from flask import Response
    return Response(buf, mimetype='application/pdf',
                    headers={'Content-Disposition': f'attachment; filename=booking_slip_{ref_no}.pdf'})










@main.route('/get_doctor_profile/<int:doctor_id>', methods=['GET'])
@login_required
def get_doctor_profile(doctor_id):
    if current_user.role.lower()!= 'patient':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.home'))
    doctor = Doctor.query.get_or_404(doctor_id)
    print(doctor)
    return render_template('patient/doct_profile.html', doctor=doctor)








@main.route('/start/book_appointment/<int:department_id>')
def view_department(department_id):
    if current_user.role.lower() != 'patient':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.home'))
    department = Department.query.get_or_404(department_id)
    doctors = Doctor.query.filter_by(department_id=department.id).all()
    return render_template('patient/departments.html', department=department , doctors=doctors)
    

@main.route('/appointment_list' , methods=['GET'])
@login_required
def booked_appointment_list():
    if current_user.role.lower() != 'patient':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.home'))
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    appointments = Appointment.query.filter_by(patient_id=patient.id).all()
    return render_template('patient/booked_appointment.html', appointments=appointments)

@main.route('/get_report/<int:appointment_id>' , methods=['GET'])
@login_required
def view_report(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    if current_user.role.lower() != 'patient' or appointment.patient.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.home'))
   
    return render_template('patient/view_report.html', appointment=appointment)


    
    













