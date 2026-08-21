# 🏥 Hospital Management System (HMS)

A full-featured web-based Hospital Management System built with **Flask + SQLAlchemy + Jinja2 + Bootstrap**, supporting **Admin, Doctor, and Patient** roles with real-time chat, video consultations, and more.

---

## 🎨 Design System

The entire application shares one design system defined in `static/css/`:

| File | Purpose |
|---|---|
| `tokens.css` | Design tokens — colors, typography, spacing, radius, elevation, motion. Single source of truth. |
| `base.css` | Reset + base element styles |
| `components.css` | Buttons, forms, cards, badges, tables, modals, dropdowns, pagination, toasts, skeletons, empty states |
| `layout.css` | Sidebar, topbar, page header, breadcrumbs, responsive shell |
| `utilities.css` | Spacing/text/flex helpers |
| `app.css` | Entry point importing the above (tokens → base → components → layout → utilities) |

Key decisions:
- **Fonts**: *Plus Jakarta Sans* for headings, *Inter* for body — exactly two families site-wide.
- **Colors**: Primary `#2563eb`, accent `#06b6d4`, full slate neutral scale, semantic success/warning/danger/info — all as CSS variables, with a complete dark-mode token set.
- **Spacing**: 4px-based scale (`--space-1` … `--space-16`).
- **Elevation**: five shadow levels (`--shadow-xs` … `--shadow-xl`) plus a shared focus ring.
- **Motion**: 150–350ms micro-interactions with a spring-like ease; `prefers-reduced-motion` respected globally.
- **Layout**: every authenticated page extends `templates/base.html` (sidebar + topbar + content shell); auth pages extend `templates/auth_base.html` (split-screen). No page defines its own colors or fonts.

---

## 🚀 Deployment Instructions (Free)

### Option 1: Local Development

```bash
# 1. Clone the project
cd hms-portal

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env to set SECRET_KEY (at minimum)

# 4. Run the app
python app.py

# 5. Open http://127.0.0.1:5000
# Default admin credentials (created on first boot):
#   Email: Ehtesham@hms.com
#   Password: Admin@2024
```

### Option 2: Render (Free Hosting)

1. Push the project to a GitHub repository.
2. Go to [dashboard.render.com](https://dashboard.render.com) → **New +** → **Web Service**.
3. Connect your GitHub repo. Render will auto-detect the `render.yaml`.
4. Set the following environment variables:
   - `SECRET_KEY`: Generate a random one (`python -c "import secrets; print(secrets.token_hex(32))"`)
   - `DATABASE_URL`: **Use a free external PostgreSQL provider** (see below)
5. Render will build and deploy automatically.

### External PostgreSQL (Free, Never Expires)

Render's free Postgres expires after ~30 days. **Use one of these instead:**

- **[Neon](https://neon.tech)** — Free tier: 0.5 GB storage, never expires.
- **[Supabase](https://supabase.com)** — Free tier: 500 MB, never expires.

1. Create a free account on Neon or Supabase.
2. Create a new database and copy the connection string (looks like `postgresql://user:password@host/dbname`).
3. Set it as the `DATABASE_URL` environment variable in Render **and remove the `?sslmode=require` query parameter** if present (SQLAlchemy handles it).

The app switches automatically between SQLite (local) and PostgreSQL (production) based on the `DATABASE_URL` scheme.

> **Upgrading an existing database:** if you already ran a previous version of this
> app, run `python migrate_db.py` once before starting to add the new columns
> (doctor daily capacity, soft-delete flag, appointment reassignment fields).
> Fresh installs create everything automatically on first boot.

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | Yes | `dev-secret-key-change-me` | Flask session signing key. Use a long random string in production. |
| `DATABASE_URL` | No | `sqlite:///hospital_management.db` | DB connection string. `postgresql://...` for production. |
| `MAIL_SERVER` | No | `smtp.gmail.com` | SMTP server for email notifications (optional). |
| `MAIL_PORT` | No | `587` | SMTP port. |
| `MAIL_USE_TLS` | No | `true` | Use TLS for SMTP. |
| `MAIL_USERNAME` | No | — | Gmail address (or other SMTP user). |
| `MAIL_PASSWORD` | No | — | Gmail app password (not your regular password). |
| `MAIL_DEFAULT_SENDER` | No | same as `MAIL_USERNAME` | From address for outgoing emails. |

If SMTP is not configured, emails are logged to the console instead of crashing.

---

## 🏗 Tech Stack

| Component | Technology |
|---|---|
| Backend | Flask 3.1, Python 3.13 |
| Database | SQLAlchemy 2.0 + SQLite (dev) / PostgreSQL (prod) |
| Real-time | Flask-SocketIO + python-socketio + eventlet |
| Frontend | Bootstrap 5, Jinja2, Chart.js, Jitsi Meet API |
| Design system | Custom CSS architecture (`tokens.css`, `components.css`, `layout.css`, `utilities.css`) |
| Email | Flask-Mail (only when configured) |
| PDF | fpdf2 |
| Auth | Flask-Login, Werkzeug password hashing, Flask-WTF CSRF |

## 🔑 Default Accounts

| Role | Email | Password |
|---|---|---|
| Admin | `Ehtesham@hms.com` | `Admin@2024` |

Doctors and patients must be registered via the app (admin can add doctors; patients self-register).

## 📁 Project Structure

```
back_app/
  models.py       # Database models (User, Doctor, Patient, Appointment, ChatMessage, VideoRoom, Notification, ReportFile, DoctorRating, etc.)
  routes.py       # All route handlers organized by role
  all_funtion.py  # Utility functions (file upload, notification helpers)
  socketio_events.py  # SocketIO event handlers (chat, typing, notifications)
  emailer.py      # Email sending with console fallback
app.py            # Flask app factory, SocketIO/CSRF/Mail init
templates/        # Jinja2 templates organized by role
static/           # CSS, JS, images, uploads
```

## ✨ What's New (Full Upgrade)

See [CHANGELOG.md](./CHANGELOG.md) for a detailed list of all features added across all four phases.