# JobPortal Pro – Python Flask

Converted from PHP ([web-Active](https://github.com/Thiwa1/web-Active)) to Python Flask.

## Stack

| Layer | Technology |
|-------|-----------|
| Framework | Flask 3.1 |
| Database | MySQL via SQLAlchemy + PyMySQL |
| Auth | Werkzeug password hashing, Flask sessions |
| Email | Flask-Mail (SMTP) |
| SMS | Notify.lk API |
| OAuth | Google OAuth 2.0 |
| Frontend | Bootstrap 5.3, FontAwesome 6, vanilla JS |

## Project Structure

```
web-active-python/
├── app.py               # App factory & entry point
├── config.py            # Environment-based config
├── database.py          # SQLAlchemy instance
├── models.py            # All ORM models (20+ tables)
├── requirements.txt
├── .env.example
├── routes/
│   ├── auth.py          # Login, register, logout, OTP, Google OAuth
│   ├── main.py          # Public pages, job search, guest apply
│   ├── employer.py      # Employer dashboard, post/manage jobs, billing
│   ├── employee.py      # Job seeker dashboard, apply, documents, alerts
│   └── admin.py         # Admin panel, approvals, reports, SMS
├── services/
│   ├── ai_recruiter.py  # CV scoring & salary estimation
│   ├── mail.py          # Email helper (Flask-Mail)
│   ├── sms.py           # SMS via Notify.lk
│   ├── recaptcha.py     # Google reCAPTCHA v3
│   ├── google_auth.py   # Google OAuth helpers
│   └── upload.py        # Secure file upload helper
├── templates/           # Jinja2 templates (Bootstrap 5)
│   ├── layout/          # base.html, header, footer, chat widget
│   ├── employer/        # 8 employer templates
│   ├── employee/        # 7 employee templates
│   └── admin/           # 9 admin templates
└── static/
    ├── css/custom.css
    ├── js/main.js
    └── uploads/         # Uploaded files (gitignored)
```

## Quick Start

### 1. Clone & install
```bash
cd web-active-python
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure environment
```bash
copy .env.example .env   # Windows
# cp .env.example .env   # Linux/Mac
```
Edit `.env` with your database credentials and API keys.

### 3. Create MySQL database
```sql
CREATE DATABASE tiptromr_vacancies CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```
Tables are created automatically on first run via SQLAlchemy.

### 4. Run
```bash
python app.py
```
Open **http://localhost:5000**

## User Roles & Default Credentials

Register via `/register`. Choose your role:

| Role | Access |
|------|--------|
| `employee` | Browse jobs, apply, manage profile & documents |
| `employer` | Post jobs, manage applications, billing |
| `admin` | Full admin panel |
| `paperadmin` | Paper ads management only |

To create your first admin, register normally then update the `user_type` in the database to `admin`.

## Features

- **Job Portal**: Browse, search, filter jobs by district/city/category/type
- **Multi-role Auth**: CSRF protection, bcrypt passwords, Google OAuth, OTP reset
- **Employer Portal**: Post jobs, manage applications, billing with payment slip upload
- **Job Seeker Portal**: Profile, CV upload, apply in one click, job alert SMS
- **Guest Applications**: Apply without registering
- **AI CV Scorer**: Keyword + experience matching (no external API needed)
- **SMS Alerts**: Auto-notify seekers when matching jobs are approved
- **Paper Ads**: Submit newspaper ads with payment slip
- **Admin Panel**: Approve jobs/payments, verify employers, SMS panel, revenue report
- **File Uploads**: CVs, logos, payment slips, job banners — stored in `static/uploads/`

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DB_HOST` | MySQL host (default: localhost) |
| `DB_NAME` | Database name |
| `DB_USER` | Database user |
| `DB_PASSWORD` | Database password |
| `SECRET_KEY` | Flask secret key (change in production!) |
| `SMTP_HOST` | SMTP server for emails |
| `SMTP_PORT` | SMTP port (default: 587) |
| `SMTP_USER` | SMTP username |
| `SMTP_PASS` | SMTP password |
| `RECAPTCHA_SITE_KEY` | Google reCAPTCHA v3 site key |
| `RECAPTCHA_SECRET_KEY` | Google reCAPTCHA v3 secret key |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `SMS_USER_ID` | Notify.lk user ID |
| `SMS_API_KEY` | Notify.lk API key |
| `SMS_SENDER_ID` | SMS sender name |

## Cloud Deployment

### Railway / Render / Heroku
Set all environment variables in the platform dashboard, then:
```bash
# Procfile
web: gunicorn app:app
```
Add `gunicorn` to `requirements.txt`.

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
```
