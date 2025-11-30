# 🏥 Hospital Management System (HMS)

A web-based Hospital Management System built using **Flask + SQLAlchemy** to manage Patients, Doctors, Appointments and Medical Records digitally.  
This application simplifies healthcare workflow by providing **online appointment booking, medical history tracking, doctor availability, reports and admin controls**.

---

## 🚀 Main Features of this Project 

### 👤 Patient Dashboard
- Register & Login securely
- Book appointments with available doctors
- View doctor profiles & departments
- View/download medical reports with prescription
- Cancel appointments & view booking history

### 🩺 Doctor Dashboard
- Manage assigned patients
- Update treatment history & prescriptions
- Add medicines dynamically
- View past reports and appointments
- Set weekly availability (Morning/Evening Slots)

### 🔐 Admin Dashboard
- Add / Edit / Delete Doctors 
- Edit / Delete / Patients
- Block/Unblock all users
- View all appointments in hospital and manage it
- Check reports of Patients

---

## 🏗 Tech Stack Used

| Component | Technology |
|----------|------------|
| Backend | Flask, Python |
| Database ORM | SQLAlchemy + SQLite |
| Frontend | HTML, CSS, Bootstrap, JS(Basic for Dyanamic)|
| Templating Engine | Jinja2 |
| Authentication | Flask-Login |
| PDF Report Support | Browser print styling |


---

## 📁 Folder Structure

MAD-1-WEB-APP/
│
├── back_app/
│   ├── models.py            # Contains all database tables using SQLAlchemy
│   ├── routes.py            # Handles routing, backend logic & page control
│   └── all_function.py      # Helper utility functions used across the system
│
├── instance/
│   └── hospital_management.db   # SQLite database / configuration directory
│
├── static/                       # Frontend assets for UI enhancement
│   ├── css/                      # Stylesheets
│   ├── img/                      # Images & icons
│   └── js/                       # JavaScript files
│
├── templates/                    # HTML pages for each user role
│   ├── admin/                    # Admin dashboard & control pages
│   ├── auth/                     # Login, Register, Profile
│   ├── doctor/                   # Doctor panel pages
│   ├── patient/                  # Appointment + Report UI
│   ├── base.html                 # Main layout template
│   └── home.html                 # Landing page
│
├── app.py                        # Runs Flask server & initializes the application
└── README.md                     # Project documentation

