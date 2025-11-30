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

MAD 1 WEB APP
│
├── back_app/
│   ├── models.py  ( Store  all tables of HMS web app )
│   ├── routes.py    ( Control all pages and button or every activity )
│   └── all_function.py  (Some important fucntion )
│
├── instance/
│   └── hospital_management.db   (or config file)    
│
├── static/    ( Make more attractive of any page and UI design )
│   ├── css/     
│   ├── img/
│   └── js/
│
├── templates/  (Template folders where pages are persent ) 
│   ├── admin/
│   ├── auth/
│   ├── doctor/
│   ├── patient/
│   └── home.html
│
├── app.py  (It starts Flask server, and runs the system.)
└── Readme.md 