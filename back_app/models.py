from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin , LoginManager


db = SQLAlchemy()

# 1. Users Table (Central table for all roles)
class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    age = db.Column(db.Integer(),  nullable=False)
    gender = db.Column(db.String(10) , nullable=False)
    role = db.Column(db.String(50), nullable=False ,default='Patient')  # 'admin', 'doctor', 'patient'
    profile_picture = db.Column(db.String(250), nullable=True, default='default.png')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    # Yeh batata hai ki ek User ya to ek Doctor ya ek Patient ho sakta hai.
    doctor = db.relationship('Doctor', backref='user', uselist=False, cascade="all, delete-orphan")
    patient = db.relationship('Patient', backref='user', uselist=False, cascade="all, delete-orphan")

# 2. Departments Table
class Department(db.Model):
    __tablename__ = 'department'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Relationship: Ek department mein kai doctors ho sakte hain.
    doctors = db.relationship('Doctor', backref='department')

# 3. Doctors Table (Specific details for doctors)
class Doctor(db.Model):
    __tablename__ = 'doctor'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    qualification = db.Column(db.String(150), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    experience_years = db.Column(db.Integer, nullable=False)
    bio = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    appointments = db.relationship('Appointment', backref='doctor')
    availabilities = db.relationship('DoctorAvailability', backref='doctor', cascade="all, delete-orphan")

# 4. Patients Table (Specific details for patients)
class Patient(db.Model):
    __tablename__ = 'patient' 
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    address = db.Column(db.String(250), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship
    appointments = db.relationship('Appointment', backref='patient')

# 5. Appointments Table
class Appointment(db.Model):
    __tablename__ = 'appointment'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    appointment_datetime = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Scheduled')  # 'Scheduled', 'Completed', 'Cancelled'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    history = db.relationship('PatientHistory', backref='appointment', uselist=False, cascade="all, delete-orphan")

# 6. Patient History Table (Connected to one appointment)
class PatientHistory(db.Model):
    __tablename__ = 'patient_history'
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False, unique=True)
    visit_type = db.Column(db.String(100))
    tests_done = db.Column(db.String(255))
    diagnosis = db.Column(db.Text)
    prescription_notes = db.Column(db.Text)
    
    # Relationship
    medicines = db.relationship('PrescribedMedicine', backref='history', cascade="all, delete-orphan")

# 7. Prescribed Medicines Table (Many medicines for one history entry)
class PrescribedMedicine(db.Model):
    __tablename__ = 'prescribe_medicine'
    id = db.Column(db.Integer, primary_key=True)
    history_id = db.Column(db.Integer, db.ForeignKey('patient_history.id'), nullable=False)
    medicine_name = db.Column(db.String(150))
    dosage = db.Column(db.String(150))

# 8. Doctor Availability Table
class DoctorAvailability(db.Model):
    __tablename__ = 'doctor_availability'
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    day_of_week = db.Column(db.String(20), nullable=False) 

    # Before Lunch Slot
    start_time_before_lunch = db.Column(db.Time, nullable=True)
    end_time_before_lunch = db.Column(db.Time, nullable=True)

    # After Lunch Slot
    start_time_after_lunch = db.Column(db.Time, nullable=True)
    end_time_after_lunch = db.Column(db.Time, nullable=True)
    is_available = db.Column(db.Boolean, default=True)

