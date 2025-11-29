from flask import render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash , generate_password_hash
from werkzeug.utils import secure_filename
from datetime import time , datetime
from .models import *
from .all_funtion import save_picture  , create_admin_user 
from flask import current_app as app
# =================================================================

@app.route('/')
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
            if user.role.lower() == 'doctor' and user.doctor.is_active:
                return redirect(url_for('doctor_dashboard'))
            elif user.role.lower() == 'patient' and user.patient.is_active:
                return redirect(url_for('patient_dashboard'))
            elif user.role.lower() == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                
                return redirect(url_for('login'))
            flash('Logged in successfully!', 'success')
        else:
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('login'))
    return render_template("auth/login.html")


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():

    if request.method == "POST":
        old_pass = request.form.get("old_password")
        new_pass = request.form.get("new_password")
        confirm_pass = request.form.get("confirm_password")

        # 1️ Old password verify
        if not check_password_hash(current_user.password, old_pass):
            flash("❌ Old password is incorrect!", "danger")
            return redirect(url_for('change_password'))

        # 2️ New password match check
        if new_pass != confirm_pass:
            flash("⚠ New & Confirm password do not match!", "warning")
            return redirect(url_for('change_password'))

        # 3️ Password update (hashing required)
        hashed_new_password = generate_password_hash(new_pass)
        current_user.password = hashed_new_password
        db.session.commit()

        flash("✅ Password updated successfully!", "success")
        return redirect(url_for('login'))  # Optional → force re-login
    return render_template("auth/profile_setting.html")


@app.route("/appointment/update_status/<int:appointment_id>/<string:new_status>")
@login_required
def update_appointment_status(appointment_id, new_status):

    valid_status = ["Scheduled", "Completed", "Cancelled", "Booked"]

    if new_status not in valid_status:
        flash("Invalid status!", "danger")
        return redirect(request.referrer)

    appointment = Appointment.query.get_or_404(appointment_id)
    appointment.status = new_status
    db.session.commit()

    flash(f"Appointment marked as {new_status}", "success")
    return redirect(request.referrer)



@app.route('/update_profile' , methods=['POST','GET'])
@login_required
def update_profile():
    if request.method == 'POST':
        user = User.query.get(current_user.id)
        user.full_name = request.form.get('full_name')

        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            
            # Check if the user selected a file (filename is not empty)
            if file.filename != '':
                # Clean the filename to ensure it's safe
                filename = secure_filename(file.filename)
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
            d_user.full_name = request.form.get('full_name')
            d_user.specialization = request.form.get('specialization')
            d_user.experiencer_years = request.form.get('experience_years')
            d_user.bio = request.form.get('bio')
        
        db.session.commit()
        
        flash("Your profile successfully , Updated!")
        return redirect('update_profile')
    else:

        user = User.query.get(current_user.id)

        return render_template('auth/profile_setting.html' , current_user=user)




# =============== Dashboard Routes ===============

@app.route('/doctor/dashboard')
@login_required
def doctor_dashboard():
    if current_user.role.lower() != 'doctor' or not current_user.doctor.is_active:
        flash('You are blocked or not Doctor, Access denied', 'danger')
        return redirect(url_for('login'))
    doctor = Doctor.query.get(current_user.doctor.id)
    appointments = Appointment.query.filter_by(doctor_id=doctor.id).order_by(Appointment.appointment_datetime.desc()).all()
    t_upcomming_appt = Appointment.query.filter(Appointment.doctor_id==doctor.id,Appointment.status=='booked').count()
    t_done_appt = Appointment.query.filter(Appointment.doctor_id==doctor.id,Appointment.status!='booked').count()
    return render_template('doctor/dashboard.html' , user=current_user, appointments=appointments , t_upcomming_appt = t_upcomming_appt , t_done_appt = t_done_appt)


@app.route('/patient/dashboard')
@login_required
def patient_dashboard():
    if current_user.role.lower() != 'patient' or not current_user.patient.is_active:
        flash('You are bloked or not Patient ,Access denied.', 'danger')
        return redirect(url_for('login'))
    flash('Welcome to your dashboard!', 'success')
    # Here you can add logic to fetch patient-specific data
    # For example, appointments, medical history, etc.
    departments = Department.query.all()
    appointments = Appointment.query.filter_by(patient_id=current_user.patient.id).all()
    upcoming_appointments_count = Appointment.query.filter(Appointment.patient_id==current_user.patient.id,Appointment.status=='booked').count()
    total_medical_record = 0
    for appt in appointments:
        if appt.status.lower() == 'completed':
            total_medical_record += 1

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
        qualification = request.form.get('qualification')
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
            qualification=qualification,
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


#

@app.route('/admin/doctor/<int:doctor_id>', methods=['GET'])
@login_required
def view_doctor(doctor_id):
    if current_user.role.lower() != 'admin':
        flash("access denied you are not admin , danger")
        return redirect(url_for('home'))
    doctor = Doctor.query.get_or_404(doctor_id)
    return render_template('admin/doctor_profile.html', doctor=doctor)

@app.route('/admin/delete_doctor/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
def delete_doctor(doctor_id):
    if current_user.role.lower() != 'admin':
        flash("access denied you are not admin , danger")
        return redirect(url_for('home'))
    doctor = Doctor.query.get_or_404(doctor_id)
    new_doctor = Doctor.query.filter_by(specialization=doctor.specialization).first()
    appointments = Appointment.query.filter_by(doctor_id=doctor.id).all()
    for appt in appointments:
        if new_doctor and appt.doctor_id != new_doctor.id and appt.status.lower() == 'booked':
            appt.doctor_id = new_doctor.id
        else:
            db.session.delete(appt)

    user = User.query.get_or_404(doctor.user_id)
    db.session.delete(doctor)
    db.session.delete(user)
    db.session.commit()
    flash('Doctor record deleted successfully!', 'success')
    return redirect(url_for('all_doctors'))

@app.route('/admin/block_doctor/<int:doctor_id>', methods=['POST','GET'])
@login_required
def block_doctor(doctor_id):
    if current_user.role.lower() != 'admin':
        flash("access denied you are not admin , danger")
        return redirect(url_for('home'))
    doctor = Doctor.query.get_or_404(doctor_id)
    user = User.query.get_or_404(doctor.user_id)
    doctor.is_active = False
    db.session.commit()
    return redirect(url_for('view_doctor', doctor_id=doctor.id))

@app.route('/admin/unblock_doctor/<int:doctor_id>', methods=['POST','GET'])
@login_required
def unblock_doctor(doctor_id):
    if current_user.role.lower() != 'admin':
        flash("access denied you are not admin , danger")
        return redirect(url_for('home'))
    doctor = Doctor.query.get_or_404(doctor_id)
    user = User.query.get_or_404(doctor.user_id)
    doctor.is_active = True
    db.session.commit()
    
    return redirect(url_for('view_doctor', doctor_id=doctor.id))

@app.route('/admin/edit_doctor/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
def edit_doctor(doctor_id):
    if current_user.role.lower() != 'admin':
        flash("access denied you are not admin , danger")
        return redirect(url_for('home'))
    doctor = Doctor.query.get_or_404(doctor_id)
    if request.method == 'POST':
        doctor.user.full_name = request.form.get('full_name')
        doctor.user.phone_number = request.form.get('phone_number')
        doctor.specialization = request.form.get('specialization')
        doctor.experience_years = request.form.get('experience_years')
        db.session.commit()
        flash('Doctor details updated successfully!', 'success')
        return redirect(url_for('all_doctors'))
    return render_template('admin/edit_doctor.html', doctor=doctor)



@app.route('/admin/patient/<int:patient_id>', methods=['GET'])
@login_required
def view_patient(patient_id):
    if current_user.role.lower() != 'admin':
        flash("access denied you are not admin , danger")
        return redirect(url_for('home'))
    patient = Patient.query.get_or_404(patient_id)
    return render_template('admin/patient_profile.html', patient=patient)

@app.route('/admin/delete_patient/<int:patient_id>', methods=['POST','GET'])
@login_required
def delete_patient(patient_id):
    if current_user.role.lower() != 'admin':
        flash("access denied you are not admin , danger")
        return redirect(url_for('home'))
    patient = Patient.query.get_or_404(patient_id)
    user = User.query.get_or_404(patient.user_id)
    appointments = Appointment.query.filter_by(patient_id=patient.id).all()
    for appointment in appointments:
        db.session.delete(appointment)
    db.session.delete(patient)
    db.session.delete(user)
    db.session.commit()
    
    return redirect(url_for('all_patients'))


@app.route('/admin/block_patient/<int:patient_id>', methods=['POST','GET'])
@login_required
def block_patient(patient_id):
    if current_user.role.lower() != 'admin':
        flash("access denied you are not admin , danger")
        return redirect(url_for('home'))
    patient = Patient.query.get_or_404(patient_id)
    user = User.query.get_or_404(patient.user_id)
    patient.is_active = False
    db.session.commit()
    
    return redirect(url_for('view_patient' , patient_id=patient.id))

@app.route('/admin/unblock_patient/<int:patient_id>', methods=['POST','GET'])
@login_required
def unblock_patient(patient_id):
    if current_user.role.lower() != 'admin':
        flash("access denied you are not admin , danger")
        return redirect(url_for('home'))
    patient = Patient.query.get_or_404(patient_id)
    user = User.query.get_or_404(patient.user_id)
    patient.is_active = True
    db.session.commit()
    
    return redirect(url_for('view_patient' , patient_id=patient.id))

@app.route('/admin/edit_patient/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def edit_patient(patient_id):
    if current_user.role.lower() != 'admin':
        flash("access denied you are not admin , danger")
        return redirect(url_for('home'))
    patient = Patient.query.get_or_404(patient_id)
    if request.method == 'POST':
        patient.user.full_name = request.form.get('full_name')
        patient.user.age = request.form.get('age')
        patient.user.phone_number = request.form.get('phone_number')
        db.session.commit()
        flash('Patient details updated successfully!', 'success')
        return redirect(url_for('all_patients'))
    return render_template('admin/edit_patient.html', patient=patient)


@app.route('/admin/patient/view_report/<int:appointment_id>')
@login_required
def admin_view_report(appointment_id):
    if current_user.role.lower() != 'admin':
        flash("Accesss denied you are not admin, Danger!")
        return redirect(url_for('home'))
    appointment = Appointment.query.get_or_404(appointment_id)
    return render_template('admin/patient_report.html' , appointment=appointment)
    




#========== Routes Manage by Doctor =============



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
@login_required
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
        if appointment.status.lower() == 'booked':
            upcomming_count = upcomming_count+1
        else:
            done_count = done_count+1
    return render_template('doctor/manage_appointment.html', appointments=appointments , upcomming_count=upcomming_count ,done_count=done_count)




@app.route("/doctor/history/save/<int:appointment_id>", methods=["POST"])
@login_required
def save_patient_history(appointment_id):

    appointment = Appointment.query.get_or_404(appointment_id)

    history = appointment.history  # existing or None

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
    meds = request.form.getlist("medicine_name[]")
    doses = request.form.getlist("dosage[]")

    for med, dose in zip(meds, doses):
        if med.strip():
            new_med = PrescribedMedicine(history_id=history.id,
                                         medicine_name=med,
                                         dosage=dose)
            db.session.add(new_med)

    db.session.commit()
    flash("History Updated Successfully ✔", "success")
    return redirect(request.referrer)





# VIEW REPORT ROUTE
# ==========================
@app.route('/doctor/view_report/<int:appointment_id>')
@login_required
def view_patient_report(appointment_id):
    if current_user.role.lower() != 'doctor':
        flash("Access denied ,Danger!")
        return redirect(url_for('home'))
    # Fetch appointment by ID
    appointment = Appointment.query.get_or_404(appointment_id)

    # Access restriction: doctor can view only his own appointment reports
    if appointment.doctor_id != current_user.doctor.id:
        flash("Unauthorized Access!", "danger")
        return redirect(url_for('doctor_dashboard'))

    return render_template("doctor/patient_report.html", appointment=appointment)

@app.route('/doctor/assigned_patients' , methods=['GET'])
@login_required
def assigned_patients():
    if current_user.role.lower() != 'doctor':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    doctor = Doctor.query.get(current_user.doctor.id)
    appointments = Appointment.query.filter_by(doctor_id=doctor.id).all()
    patient_count = len(appointments)
    return render_template('doctor/assigned_patient.html', appointments=appointments , patient_count=patient_count)


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




#== Patient Book Appointment and Medical Records ===
def format_time(t):
    if t:
        return t.strftime("%I:%M %p")
    return None


@app.route('/doctor_availability/for_patient/<int:doctor_id>', methods=['GET'])
@login_required
def doctor_availability(doctor_id):
   
    doctor = Doctor.query.get_or_404(doctor_id)
    
    # Fetch availability from DB
    availabilities = DoctorAvailability.query.filter_by(doctor_id=doctor.user.id).all()
    
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

    return render_template('auth/doct_availability.html', doctor=doctor, schedule=schedule_data, week_days=week_days)


@app.route('/book_appointment_slot', methods=['POST'])
@login_required
def book_appointment_slot():
    if current_user.role.lower() != 'patient':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    
    try:
        doctor_id = request.form.get("doctor_id")
        patient_id = request.form.get("current_user.patient.id")
        slot_time = request.form.get("slot_time")      # example -> "08:00"
        appointment_date = request.form.get("appointment_date")  # yyyy-mm-dd format

        # Convert Date + Time to a combined datetime
        final_datetime = datetime.strptime(f"{appointment_date} {slot_time}", "%Y-%m-%d %H:%M:%S")

        # check already booked? (Prevent duplicate)
        existing = Appointment.query.filter_by(
            doctor_id=doctor_id,
            patient_id=current_user.patient.id,
            appointment_datetime=final_datetime
        ).first()

        if existing:
            flash("You already booked this slot!", "warning")
            return redirect(url_for('doctor_availability', doctor_id=doctor_id))

        # Save in DB
        new_appt = Appointment(
            doctor_id = doctor_id,
            patient_id = current_user.patient.id,
            appointment_datetime = final_datetime,
            status = "booked"
        )
        db.session.add(new_appt)
        db.session.commit()

        flash("Appointment booked successfully!", "success")
        return redirect(url_for('booked_appointment_list'))

    except Exception as e:
        print(e)
        flash("Something went wrong. Please try again.", "danger")
        return redirect(url_for('doctor_availability', doctor_id=doctor_id))










@app.route('/get_doctor_profile/<int:doctor_id>', methods=['GET'])
@login_required
def get_doctor_profile(doctor_id):
    if current_user.role.lower()!= 'patient':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    doctor = Doctor.query.get_or_404(doctor_id)
    print(doctor)
    return render_template('patient/doct_profile.html', doctor=doctor)








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

@app.route('/get_report/<int:appointment_id>' , methods=['GET'])
@login_required
def view_report(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    if current_user.role.lower() != 'patient' or appointment.patient.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
   
    return render_template('patient/view_report.html', appointment=appointment)


    
    












