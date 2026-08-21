# Changelog — HMS Portal Full Upgrade

All four phases of the upgrade have been implemented on top of the existing
Flask + SQLAlchemy + Jinja2 + Bootstrap structure. No feature that worked
before was removed; everything below was added or fixed.

---

## Doctor Deletion, Capacity Limits & Booking Slips

### Feature 1 — Safe Doctor Deletion (soft-delete + auto-reassignment)
- **Root-cause crash fix**: deleting a doctor no longer crashes with `NOT NULL constraint failed: video_room.appointment_id`. Cascade relationships are now explicit — `VideoRoom`, `DoctorRating`, `ChatMessage`, `PatientHistory`, and `ReportFile` all use `cascade="all, delete-orphan"` on their appointment relationship, so deleting/cleaning an appointment correctly deletes its children instead of trying to null NOT NULL FKs.
- **Soft-delete**: `User.is_deleted` field added. Deleting a doctor sets `doctor.is_active=False` + `user.is_deleted=True` (the row is never removed). The doctor disappears from all listings, search, and booking pages, and can no longer log in.
- **Patient data is never deleted**: past/completed/cancelled appointments, medical history, prescriptions, chat, and video records remain intact and still link to the (now-inactive) doctor.
- **Automatic reassignment**: on delete, every future booked appointment is either:
  - reassigned to another active doctor in the same department (with availability & capacity at that time), flagged with `reassigned_from_doctor_id`, `reassigned_at`; **or**
  - flagged `needs_reassignment=True` for manual admin action.
- **Patient notification**: affected patients get an in-app notification (and an email if SMTP is configured) for both reassigned and needs-rescheduling cases.
- **Admin confirmation screen** (`/admin/delete_doctor/<id>`): shows upcoming count, how many will auto-reassign vs. need attention, a per-appointment breakdown, and requires an explicit confirm — no more accidental single-click deletion.
- **Manual reassignment UI**: appointments flagged `needs_reassignment` appear in a warning card on the admin dashboard with a per-appointment doctor dropdown and a POST route (`/admin/appointment/<id>/reassign`).

### Feature 2 — Daily Appointment Capacity per Doctor
- `Doctor.max_appointments_per_day` field (default 20), editable per-doctor from the admin Edit Doctor page.
- Enforced at booking time: non-cancelled appointments for a doctor+date are counted; once the cap is reached the booking POST is rejected with a message naming the **next available day**.
- Calendar picker is capacity-aware: full days render with a red strikethrough and are not selectable; clicking one shows a toast; the slots panel shows a `booked/max` badge; an info banner on the booking page highlights the next day with open slots.
- Load visibility: the admin doctors table shows a `booked/max` progress bar per doctor; the doctor's own dashboard shows a "X/Y booked today" progress bar.

### Feature 3 — Appointment Booking Confirmation Slip
- After a successful booking the patient is taken straight to a **ticket-style confirmation slip** page (`/booking/<id>/slip`) with animated entrance, torn-perforation design, doctor photo/name/dept, date & time, patient name, `HMS-XXXXX` reference number, "Confirmed" status, and a "please arrive 10 minutes early" note.
- **Downloadable PDF** at `/booking/<id>/slip_pdf` (fpdf2, styled letterhead slip).
- **Persistent dashboard slip**: the patient dashboard shows a compact "Next Upcoming Appointment" slip card with a **"Updated" badge** when the appointment was reassigned or rescheduled, and a View Slip button.
- Reassignment automatically refreshes the slip (new doctor/time shown) and marks it updated.

### Database changes (run once: `python migrate_db.py`)
| Table | New column |
|---|---|
| `user` | `is_deleted` BOOLEAN DEFAULT 0 |
| `doctor` | `max_appointments_per_day` INTEGER DEFAULT 20 |
| `appointment` | `reassigned_from_doctor_id` INTEGER → doctor(id) |
| `appointment` | `needs_reassignment` BOOLEAN DEFAULT 0 |
| `appointment` | `reassigned_at` DATETIME |

Files touched: `back_app/models.py`, `back_app/routes.py`, `static/js/calendar-picker.js`, `static/css/calendar.css`, `static/css/components.css`, `templates/patient/booking_slip.html`, `templates/patient/dashboard.html`, `templates/patient/booking_slip.html`, `templates/admin/confirm_delete_doctor.html`, `templates/admin/dashboard.html`, `templates/admin/all_doctors.html`, `templates/admin/edit_doctor.html`, `templates/admin/doctor_profile.html`, `templates/doctor/dashboard.html`, `templates/auth/doct_availability.html`, new `migrate_db.py`.

---

## Doctor Onboarding — Auto-Generated Credentials

- **Admin creates a doctor with only 3 fields**: full name, email, and department/specialization (the form no longer demands phone/age/gender/qualification/bio upfront).
- **Auto-generated temporary password**: a random password (`Doc@xxxxxxxx`) is created and hashed with Werkzeug — the old hardcoded `Doctor@2024` is gone.
- **Credentials emailed automatically** to the doctor's address via Flask-Mail using a styled welcome email. If SMTP is not configured, the full email content (including the password) is printed to the server console so the flow still works in development.
- **The generated password is also flashed** to the admin after creation, so it can be shared if email is unavailable.
- **Doctor completes their profile after first login**: Profile Settings now lets doctors update phone number, age, gender, specialization, qualification, experience, and bio (placeholders like `0000000000` / `Not specified` are shown empty and get replaced).
- **Password change flow** remains available under Profile Settings → Security.
- **Bug fixed**: the doctor profile-update route had a `experiencer_years` typo and wrongly set `full_name` on the `Doctor` model — both corrected so profile saves actually persist.

---

## Phase 1 — Foundation, Security, and Doctor–Patient Interaction

### Security hardening
- Passwords confirmed hashed with Werkzeug (`generate_password_hash` / `check_password_hash`) everywhere; no plain-text storage remains.
- `SECRET_KEY` and `DATABASE_URL` now come from environment variables loaded via `python-dotenv`. Added `.env.example` documenting every variable (no real secrets).
- CSRF protection enabled globally via Flask-WTF (`CSRFProtect`) on all POST forms (login, register, profile, booking, availability, doctor history, admin forms, chat upload, video start/end, notifications). Verified that a POST without a token is rejected (400).
- File upload validation: profile pictures restricted to image extensions; chat and lab-file uploads restricted to `png/jpg/jpeg/gif/webp/pdf/doc/docx/txt`, max 10 MB per file, global 16 MB request cap.
- Authorization gaps fixed:
  - Login no longer crashes when the email doesn't exist (was a 500).
  - `update_appointment_status` now restricts actions: patients may only cancel their own appointments; doctors only complete/cancel their own; admin full control.
  - `save_patient_history` restricted to the assigned doctor or admin.
  - `set_availability` restricted to doctors and uses the correct `doctor.id` (was using `user.id` — bug fixed).
  - `doctor_availability` and `check_availability` lookup by `doctor.id` (bug fixed).
  - All report/chat/video routes enforce participant ownership (patient + doctor + admin).
  - Fixed `url_for` endpoints missing the `main.` blueprint prefix (template + routes).

### Real-time chat (Doctor ↔ Patient)
- New `ChatMessage` model scoped to a single appointment.
- Real-time messaging via Flask-SocketIO (typing indicator, timestamps, read/unread ✓/✓✓).
- File/image attachments inside chat (max 10 MB, restricted extensions) via `/chat/<id>/upload`.
- "Chat" button next to every booked/completed appointment on both patient and doctor appointment lists, plus the appointment details page.
- Chat room restricted to the appointment's patient and doctor (admin oversight allowed).
- Message history REST endpoint `/chat/<id>/messages`.

### Video consultation
- New `VideoRoom` model (unique unguessable room name, status pending/active/ended, start/end timestamps).
- Jitsi Meet public server via its External API — no API key or signup required.
- "Video Call" buttons on chat page and appointment lists; Start/End Call actions update room status; the other party is notified in-app when a call starts.

### In-app notifications
- New `Notification` model (recipient, title, message, link, read flag, timestamp).
- Triggers: new chat message, video call started, appointment booked, appointment status changed (completed/cancelled).
- Real-time browser push over the same SocketIO connection; notification bell with unread badge and dropdown on all dashboards.
- REST endpoints: `GET /notifications`, `GET /notifications/unread_count`, `POST /notifications/mark_read/<id>`, `POST /notifications/mark_all_read`.

### Deployment readiness
- `requirements.txt` cleaned: removed unused/broken entries (`v==1`, `extensions`, `matplotlib`, `pandas`, `numpy`, etc.), pinned versions, added `Flask-SocketIO`, `python-socketio`, `python-engineio`, `eventlet`, `python-dotenv`, `Flask-Mail`, `fpdf2`.
- `Procfile` updated to `gunicorn --worker-class eventlet` so WebSockets work in production.
- Added `render.yaml` for one-click Render deployment.
- Added `.gitignore` excluding `.env`, `__pycache__`, the `instance/` SQLite folder, and uploaded files.
- Database: `DATABASE_URL` works with SQLite locally and PostgreSQL in production (SQLAlchemy handles both). Recommend Neon/Supabase free Postgres so the DB never expires on Render's free tier (Render free Postgres expires after ~30 days).

---

## Phase 2 — Modern, Animated UI/UX Redesign

### Global design system
- New `static/css/app.css` + `static/js/app.js` providing: dark mode (persisted in `localStorage`), animated toast notifications, 3D tilt cards, count-up animations, scroll-reveal, skeleton loaders, glassmorphism, gradient stat cards.
- Flask `flash()` messages are now rendered as animated toasts site-wide instead of static alerts.
- Dark mode toggle added to the landing page and all dashboards.

### Home / landing page
- Animated gradient hero with floating blurred 3D blobs and a subtle grid pattern.
- Glassmorphism navbar (blurred, compact on scroll).
- Typewriter headline effect.
- Glowing/lift hover CTAs.
- Scroll-reveal on all sections; doctor cards are tilt-on-hover with star ratings and review counts; count-up hero stats.

### Doctor cards
- 3D tilt-on-hover following the mouse (perspective rotation) with a soft radial glow.
- Profile image zoom on hover.
- Star rating display (real data wired in Phase 4).

### Dashboard stat cards (Admin / Doctor / Patient)
- Count-up number animation when scrolled into view.
- Icon pulse on load.
- Distinct gradient backgrounds per metric.

### Interactivity and usability
- Dark mode toggle persisted in `localStorage`.
- Interactive calendar-style date + time-slot picker replaced the modal date picker on the booking page (`static/js/calendar-picker.js`), with booked slots greyed out and smooth slot-load animations.
- Loading skeleton placeholders for the live doctor search.
- Responsive pass: navbars, cards, chat, video, and dashboards adapt to mobile widths.

---

## Phase 3 — Missing Functional Features

### Search, filter, and pagination
- Server-side search + filters + pagination on:
  - Admin → All Doctors (search by name/email/specialization, filter by department/status).
  - Admin → All Patients (search by name/email, filter by status).
  - Admin → All Appointments (search by patient/doctor, filter by status and date range).
  - Patient → Find a Doctor (search by name/specialization, filter by department/specialization).

### Admin analytics dashboard
- Chart.js charts computed server-side from real DB queries:
  - Appointments booked per day (last 14 days) — bar chart.
  - Appointment status breakdown — doughnut chart.
  - Patient count by department — horizontal bar chart.
  - Doctor workload (appointments handled) — bar chart.

### Email notifications
- Flask-Mail integration for appointment booked / confirmed / cancelled / completed.
- Configured via env vars (`MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, ...); if SMTP is not configured, emails are logged to the console instead of crashing.

### Medical report / lab file uploads
- Doctors can attach lab reports/scans/PDFs (multiple files) to a patient's appointment record via the history modal.
- Files are listed with View/Download links on the doctor's, patient's, and admin's report pages.

### Proper PDF prescriptions
- Real PDF generation with `fpdf2` (`/report/pdf/<appointment_id>`): hospital letterhead header, doctor info, patient info, date, diagnosis, tests, prescribed medicines table with dosage, notes, and footer.
- Downloadable from the doctor's, patient's, and admin's report view pages (replaces browser-print styling).

---

## Phase 4 — Polish, Trust Features, and Final QA

### Ratings and reviews
- New `DoctorRating` model; a patient can rate (1–5 stars) + review a doctor only after an appointment is Completed (per-appointment, one rating, updateable).
- Average rating and review count shown on doctor cards and the doctor profile page; a dedicated reviews page lists all written reviews.

### Doctor discovery
- Live filtering search (name/specialization) + department/specialization dropdowns on the patient doctor listing — updates cards via AJAX without a full page reload, with skeleton loaders.

### Patient medical history timeline
- New visual timeline page (`/patient/medical_history`) showing all completed visits in chronological order: doctor, date, diagnosis, tests, medicines, with a link to each report.

### Error handling and validation
- Custom styled 404 and 500 error pages matching the new design.
- Server-side validation added to register (required fields, password length, email format, age range, phone format) and login (missing role/fields), plus rating range validation and booking date/time validation.

### Final end-to-end QA
- All three roles' flows smoke-tested: patient (register → login → browse → book → chat → video → report → PDF → rate → history), doctor (login → availability → history+file upload → PDF), admin (dashboard charts → search/filter/paginate → add/block/edit → view reports → notifications). CSRF rejection, SocketIO handshake, file uploads, and PDF output verified.

---

## Setup

1. `pip install -r requirements.txt`
2. `cp .env.example .env` and fill in `SECRET_KEY` (and optionally email/DB values).
3. `python app.py` — runs on `http://127.0.0.1:5000` with SQLite by default.
4. Default admin (created on first boot): email `Ehtesham@hms.com`, password `Admin@2024`.
