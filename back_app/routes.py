from flask import render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash , generate_password_hash
from datetime import time
from .models import *
from .all_funtion import save_picture  , create_admin_user 
from flask import current_app as app
# =================================================================

@app.route('/' )
def home():
    return render_template('home.html')


# =========================Authentication Routes==================


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone_number = request.form.get('phone_number')
        age = request.form.get('age')
        gender = request.form.get('gender')
        role = request.form.get('role')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please log in.', 'warning')
            return redirect(url_for('login'))

        new_user = User(
            full_name=full_name,
            email=email,
            password=generate_password_hash(password),  # Hashing should be done here
            phone_number=phone_number,
            age=age,
            gender=gender,
            role=role,
        )
            
        
        add_patient = Patient(
            user=new_user,
            gender = gender

            )



        db.session.add(new_user)
        db.session.add(add_patient)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template("auth/register.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        role = request.form.get('role')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.role.lower() == role.lower() and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            if user.role.lower() == 'doctor':
                return redirect(url_for('doctor_dashboard'))
            elif user.role.lower() == 'patient':
                return redirect(url_for('patient_dashboard'))
            elif user.role.lower() == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('home'))
        else:
            flash('Invalid email or password.', 'danger')
    return render_template("auth/login.html")


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


@app.route('/update_profile' , methods=['POST','GET'])
@login_required
def update_profile():
    if request.method == 'POST':
        user = User.query.get(curren_user.id)
        user.full_name = request.form.get('full_name')
        user.profile_picture = request.form.get('profile_pic')
        
        if current_user.role.lower() == 'patient':
            p_user = Patient.quesry.get(user_id=current_user.id)
            p_user.date_of_birth = request.form.get('date_of_birth')
            p_user.gender = request.form.get('gender')
            p_user.address = request.form.get('address')

        elif current_user.role.lower() == 'doctor':
            d_user  = Doctor.query.get(user_id=current_user.id)
            d_user.full_name = request.form.get('full_name')
            d_user.specialization = request.form.get('specialization')
            d_user.experiencer_years = request.form.get('experience_years')
            d_user.bio = request.form.get('bio')
        
        db.session.commit()
        flash("Your profile successfully , Updated!")
        if curent_user.role.lower()=='patient':
            return render_template('patient/dashboard.html')
        elif curent_user.role.lower()=='doctor':
            return render_template('doctor/dashboard.html')
    return render_template('auth/profile_setting.html')

# @app.route('/profile/update', methods=['POST'])
# @login_required
# def update_profile():
#     if request.files['profile_pic']:
#         # save_picture function ko call kiya
#         picture_file = save_picture(request.files['profile_pic'])
#         current_user.profile_picture = picture_file
#         db.session.commit()
#     # ...
#     return redirect(url_for('profile'))

 
# @app.route('/profile')
# @login_required
# def view_profile():
#     if current_user.role.lower() == 'doctor':
#         return render_template('docotr/view_Profile.html')
#     elif current_user.role.lower() == 'patient':
#         return render_template('patient/')
#     return render_template('profile.html')





# =============== Dashboard Routes ===============

@app.route('/doctor/dashboard')
@login_required
def doctor_dashboard():
    if current_user.role.lower() != 'doctor':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    return render_template('doctor/dashboard.html' , user=current_user)


@app.route('/patient/dashboard')
@login_required
def patient_dashboard():
    if current_user.role.lower() != 'patient':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    flash('Welcome to your dashboard!', 'success')
    # Here you can add logic to fetch patient-specific data
    # For example, appointments, medical history, etc.
    departments = Department.query.all()
    appointments = Appointment.query.filter_by(patient_id=current_user.id).all()
    upcoming_appointments_count = Appointment.query.filter(Appointment.patient_id==current_user.id,Appointment.status=='booked').count()
    total_medical_record = Appointment.query.filter_by(patient_id = current_user.id).count()

    return render_template('patient/dashboard.html' , user=current_user , departments=departments , appointments=appointments , upcoming_appointments_count=upcoming_appointments_count , total_medical_record=total_medical_record)



@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role.lower() != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    appointments = Appointment.query.order_by(Appointment.appointment_datetime.desc()).all()
    doctors = Doctor.query.all()
    patients = Patient.query.all()
    total_appointments = Appointment.query.count()
    total_doctors = Doctor.query.count()
    total_patients = Patient.query.count()
    return render_template('admin/dashboard.html' , user=current_user , appointments=appointments , doctors=doctors , patients=patients , total_appointments=total_appointments , total_doctors=total_doctors , total_patients=total_patients)





#========================= admin controller routes =========================


@app.route('/admin/doctors',methods=['GET'])
@login_required
def all_doctors():
    if current_user.role.lower() != 'admin':
        flash("you are nod admin access denied , DANGER!")
        return redirect(url_for('home'))
    all_doctor = Doctor.query.all()
    return render_template('/admin/all_doctors.html' , doctors = all_doctor)


@app.route('/admin/patients',methods=['GET'])
@login_required
def all_patients():
    if current_user.role.lower() != 'admin':
        flash("you are nod admin access denied , DANGER!")
        return redirect(url_for('home'))
    all_patient = Patient.query.all()
    return render_template('/admin/all_patients.html' , patients = all_patient)

@app.route('/admin/appointments',methods=['GET'])
@login_required
def all_appointments():
    if current_user.role.lower() != 'admin':
        flash("you are nod admin access denied , DANGER!")
        return redirect(url_for('home'))
    all_appointment = Appointment.query.all()
    return render_template('/admin/all_appointment.html' , appointments = all_appointment)


@app.route('/admin/add_doctor', methods=['GET', 'POST'])
@login_required
# @admin_required
def add_doctor():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        experience_year = request.form.get('experience_year')
        phone_number = request.form.get('phone_number')
        specialization = request.form.get('specialization')
        age = request.form.get('age')
        gender = request.form.get('gender')
        bio = request.form.get('bio')
        hashed_password = generate_password_hash('Doctor@2024')
        dep = Department.query.filter_by(name=specialization).first()
        if not dep:
            dep = Department(name=specialization , description=f'Department of {specialization}')
            db.session.add(dep)
            db.session.commit()
        dep_id = dep.id
        new_doctor = User(
            full_name=full_name,
            email=email,
            password=hashed_password,
            phone_number=phone_number,
            age=age,
            gender=gender,
            role='doctor'
        )
        doctor_data = Doctor(
            department_id=dep_id,
            specialization=specialization,
            experience_years=experience_year,
            bio = bio,
            user = new_doctor

        )
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please use a different email.', 'warning')
            return redirect(url_for('add_doctor'))


        db.session.add(new_doctor)
        db.session.add(doctor_data)
        db.session.commit()


        flash('Doctor added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/add_doctor.html')


# @app.route('/all_patients' , methods=["GET"])
# def patient_list():
#     if current_user.role.lower() != 'admin':
#         flash("access denied you are not admin , danger")
#         return redirect(url_for('home'))
#     return render_template('admin/all_appointment.html')



#========== Routes Manage by Doctor =============

@app.route('/patient/report', methods=['GET', 'POST'])
@login_required
def update_medical_report():
    if current_user.role.lower() != 'patient':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    if request.method == 'POST':
        report_details = request.form.get('report_details')
        new_report = MedicalReport(
            report_details=report_details,
            patient_id=patient.id
        )
        db.session.add(new_report)
        db.session.commit()
        flash('Medical report added successfully!', 'success')
        return redirect(url_for('medical_report'))
    reports = MedicalReport.query.filter_by(patient_id=patient.id).all()
    # return render_template('patient/medical_report.html', reports=reports)

@app.route('/weekly/provide_availability' , methods=['POST' , 'GET'])
@login_required
def set_availability():
    # Maan lete hain ki 'current_user' hi 'doctor' object hai
    # Agar nahi, toh aapko doctor ko fetch karna hoga, jaise:
    # doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    # doctor_id = doctor.id
    doctor_id = current_user.id # Abhi ke liye yeh maan lete hain

    # 2. Apne fixed time slots ko Python 'time' objects me define karein
    # Yeh HTML ke 'slot1' aur 'slot2' se match honge
    MORNING_START = time(8, 0, 0)  # 08:00 AM
    MORNING_END = time(12, 0, 0) # 12:00 PM
    EVENING_START = time(16, 0, 0) # 04:00 PM
    EVENING_END = time(21, 0, 0) # 09:00 PM

    if request.method == 'POST':
        try:
            days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            
            for day in days:
                # 3. Check karein 'Not Available' switch ON hai ya nahi
                is_off = f'{day}-off' in request.form
                
                # Default values ko None set karein
                start_morning = None
                end_morning = None
                start_evening = None
                end_evening = None

                # 4. Agar doctor OFF nahi hai, tabhi slots check karein
                if not is_off:
                    available_slots = request.form.getlist(day) # Jaise ['slot1', 'slot2']
                    
                    if 'slot1' in available_slots:
                        start_morning = MORNING_START
                        end_morning = MORNING_END
                    
                    if 'slot2' in available_slots:
                        start_evening = EVENING_START
                        end_evening = EVENING_END
                
                # 5. Database update/create karein (Aapke Model ke hisaab se)
                
                # Pehle check karein ki entry hai ya nahi
                avail = DoctorAvailability.query.filter_by(
                    doctor_id=doctor_id, 
                    day_of_week=day.capitalize() # 'monday' ko 'Monday' banakar save karein
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

            # 6. Database me changes save karein
            db.session.commit()
            flash('Availability updated successfully!', 'success')
            
        except Exception as e:
            db.session.rollback() 
            flash(f'Error updating availability: {e}', 'danger')

        return redirect(url_for('set_availability'))

    # GET Request: Jab page load ho, toh purani settings dikhayein
    
    # Doctor ki current availability DB se fetch karein
    current_availability_db = DoctorAvailability.query.filter_by(doctor_id=doctor_id).all()
    
    # Ise ek simple dictionary me badal dein taaki template me bheja ja sake
    # Key: 'monday', Value: poora 'avail' object
    availability_data = {}
    for item in current_availability_db:
        day_name = item.day_of_week.lower() # 'Monday' ko 'monday'
        availability_data[day_name] = item # Poora object save kar rahe hain

    return render_template('doctor/provide_availability.html', availability_data=availability_data)

    



@app.route('/doctor/appoitment',methods=['GET','POST'])
def manage_appointment():
    if current_user.role.lower() != 'doctor':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    appointments = Appointment.query.filter_by(doctor_id=doctor.id).all()
    patients = Patient.query.filter_by(user_id=current_user.id).all()
    upcomming_count = 0
    done_count = 0
    for appointment in appointments:
        if appointment:
            upcomming_count = upcomming_count+1
        else:
            done_count = done_count+1
    return render_template('doctor/manage_appointment.html', appointments=appointments , upcomming_count=upcomming_count ,done_count=done_count)





#=========================================== Routes Manage by Patient ===============================



@app.route('/check_availability/<int:doctor_id>' , methods=['GET'])
@login_required
def check_availability(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    appointments = Appointment.query.filter_by(doctor_id=doctor.id).all()
    available_slots = DoctorAvailability.query.filter_by(doctor_id=doctor.id).all()
    return render_template('patient/check_availability.html', available_slots=available_slots, booked_slots=booked_slots)


#=====view Doctor Profile and all doctors =======

@app.route('/doctor_profile/<int:doctor_id>' , methods=['GET'])
@login_required
def doctor_profile(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    return render_template('patient/doctor_profile.html', doctor=doctor)


@app.route('/doctor_list' , methods=['GET'])
@login_required
def doctor_list():
    if current_user.role.lower() != 'patient':
        flash("access denied , DANGER !")
        return redirect(url_for('home'))
    doctors = Doctor.query.all()
    departments = Department.query.all()
    return render_template('patient/all_doctors.html', doctors=doctors , departments = departments)




#== Patient Appointment and Medical Records ===

@app.route('/start/book_appointment/<int:department_id>')
def view_department(department_id):
    if current_user.role.lower() != 'patient':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    department = Department.query.get_or_404(department_id)
    doctors = Doctor.query.filter_by(department_id=department.id).all()
    return render_template('patient/departments.html', department=department , doctors=doctors)
    

@app.route('/appointment_list' , methods=['GET'])
@login_required
def booked_appointment_list():
    if current_user.role.lower() != 'patient':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    appointments = Appointment.query.filter_by(patient_id=patient.id).all()
    return render_template('patient/booked_appointment.html', appointments=appointments)


@app.route('/medical_records' ,  methods=['GET'])
@login_required
def medical_record():
    if current_user.role.lower() != 'patient':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    medical_records = PatientHistory.query.join(Appointment).filter(Appointment.patient_id == patient.id).all()
    return render_template('patient/medical_record.html', medical_records=medical_records)

@app.route('/get_report/<int:appointment_id>' , methods=['GET'])
@login_required
def view_report(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    if current_user.role.lower() != 'patient' or appointment.patient.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    # Assuming there's a relationship to fetch the report
    report = PatientHistory.query.filter_by(appointment_id=appointment.id).first()
    return render_template('patient/view_report.html', report=report)





# @app.route('/user/change_pwd' , methods=['POST','GET'])
# @login_required
# def change_password():
#     old_pass = request.query.get('old_password')
#     new_pass = request.query.get('new_password')
#     confirm_pass = request.query.get('confirm_password')
#     if new_pass != confirm_pass:
#         flash("Password do not match!" , "Danger")
#         return 
    
    












