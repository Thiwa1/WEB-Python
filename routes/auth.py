import os
import secrets
import logging
from datetime import datetime, timedelta
from functools import wraps

from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash, current_app, jsonify)
from werkzeug.security import generate_password_hash, check_password_hash

from database import db
from models import User, EmployerProfile, EmployeeProfileSeeker
from services import recaptcha, mail as mail_svc
from services.google_auth import get_auth_url, exchange_code, get_user_info

auth_bp = Blueprint('auth', __name__)

ROLE_REDIRECT = {
    'employer':   'employer.dashboard',
    'admin':      'admin.dashboard',
    'employee':   'employee.dashboard',
    'candidate':  'employee.dashboard',
    'seeker':     'employee.dashboard',
    'paperadmin': 'admin.paper_ads',
}


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('auth.login'))
            if session.get('user_type', '').lower() not in [r.lower() for r in roles]:
                flash('Access denied.', 'danger')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated
    return decorator


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    csrf_token = secrets.token_hex(32)
    session['csrf_token'] = csrf_token

    if request.method == 'POST':
        try:
            if request.form.get('csrf_token') != session.get('csrf_token'):
                raise ValueError('Security token mismatch. Please try again.')

            recaptcha_token = request.form.get('recaptcha_token', '')
            if not recaptcha.verify(recaptcha_token, 'login'):
                raise ValueError('Security check failed. Please try again.')

            email = request.form.get('user_email', '').strip().lower()
            password = request.form.get('user_password', '')

            if not email or not password:
                raise ValueError('Please fill in all fields.')

            user = User.query.filter_by(user_email=email).first()
            if not user:
                raise ValueError('Invalid email or password.')

            if user.user_block:
                raise ValueError('This account has been suspended. Contact support.')

            db_hash = user.user_password
            if isinstance(db_hash, (bytes, bytearray)):
                db_hash = db_hash.decode('utf-8', errors='replace').strip()

            if not check_password_hash(db_hash, password):
                raise ValueError('Invalid email or password.')

            session.clear()
            session['user_id'] = user.id
            session['user_type'] = user.user_type.strip()
            session['full_name'] = user.full_name
            session['last_login'] = int(datetime.utcnow().timestamp())
            session['is_paper_admin'] = int(user.is_paper_admin or 0)

            role = user.user_type.strip().lower()

            # Log admin logins
            if role in ('admin', 'paperadmin') or session['is_paper_admin']:
                try:
                    from models import AdminLoginLog
                    log = AdminLoginLog(user_id=user.id, ip_address=request.remote_addr)
                    db.session.add(log)
                    db.session.commit()
                except Exception:
                    db.session.rollback()

            # Dual-role redirect
            if session['is_paper_admin'] and role not in ('paperadmin', 'admin'):
                return redirect(url_for('main.select_dashboard'))

            dest = ROLE_REDIRECT.get(role, 'main.index')
            return redirect(url_for(dest))

        except ValueError as e:
            flash(str(e), 'danger')

    google_url = ''
    try:
        google_url = get_auth_url()
    except Exception:
        pass

    return render_template('login.html', csrf_token=csrf_token,
                           recaptcha_site_key=current_app.config.get('RECAPTCHA_SITE_KEY', ''),
                           google_url=google_url)


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    csrf_token = secrets.token_hex(32)
    session['csrf_token'] = csrf_token

    if request.method == 'POST':
        try:
            if request.form.get('csrf_token') != session.get('csrf_token'):
                raise ValueError('Security check failed (CSRF).')

            recaptcha_token = request.form.get('recaptcha_token', '')
            if not recaptcha.verify(recaptcha_token, 'register'):
                raise ValueError('Security check failed (reCAPTCHA).')

            full_name = request.form.get('full_name', '').strip()
            user_email = request.form.get('user_email', '').strip().lower()
            user_password = request.form.get('user_password', '')
            birthday_str = request.form.get('Birthday', '')
            gender = request.form.get('male_female', 'Not Specified')
            user_type = request.form.get('user_type', '').strip()
            mobile = ''.join(c for c in request.form.get('mobile_number', '') if c.isdigit() or c == '+')
            whatsapp = ''.join(c for c in request.form.get('WhatsApp_number', mobile) if c.isdigit() or c == '+')
            company_name = request.form.get('company_name', '').strip()
            country = request.form.get('country', 'Sri Lanka').strip()

            if not user_email or '@' not in user_email:
                raise ValueError('A valid email address is required.')
            if len(user_password) < 8:
                raise ValueError('Password must be at least 8 characters.')
            if not birthday_str:
                raise ValueError('Birthday is required.')

            birthday = datetime.strptime(birthday_str, '%Y-%m-%d').date()

            if User.query.filter_by(user_email=user_email).first():
                raise ValueError('This email is already registered.')

            hashed = generate_password_hash(user_password, method='pbkdf2:sha256')

            user = User(
                user_email=user_email,
                user_password=hashed.encode(),
                full_name=full_name,
                Birthday=birthday,
                male_female=gender,
                user_type=user_type,
                mobile_number=mobile,
                WhatsApp_number=whatsapp,
                country=country,
                user_active=1,
                user_block=0,
            )
            db.session.add(user)
            db.session.flush()

            if user_type.lower() == 'employer':
                profile = EmployerProfile(
                    link_to_user=user.id,
                    employer_name=company_name or full_name,
                    employer_mobile_no=mobile,
                    employer_whatsapp_no=whatsapp,
                )
            else:
                profile = EmployeeProfileSeeker(
                    link_to_user=user.id,
                    employee_full_name=full_name,
                )
            db.session.add(profile)
            db.session.commit()

            try:
                body = f"""
                <h2>Welcome, {full_name}!</h2>
                <p>Your account has been created successfully.</p>
                <p><a href='{current_app.config["APP_URL"]}/login'>Login Here</a></p>
                """
                mail_svc.send_email(user_email, 'Welcome to JobPortal Pro!', body)
            except Exception:
                pass

            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))

        except ValueError as e:
            db.session.rollback()
            flash(str(e), 'danger')
        except Exception as e:
            db.session.rollback()
            logging.error(f"Registration error: {e}")
            flash('An unexpected error occurred. Please try again.', 'danger')

    from models import UserType
    user_types = UserType.query.filter_by(type_hide=0).all()
    return render_template('register.html', csrf_token=csrf_token, user_types=user_types,
                           recaptcha_site_key=current_app.config.get('RECAPTCHA_SITE_KEY', ''))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('user_email', '').strip().lower()
        user = User.query.filter_by(user_email=email).first()
        if user:
            otp = str(secrets.randbelow(900000) + 100000)
            user.send_opt = int(otp)
            user.send_time = datetime.utcnow()
            user.max_validate_time = 10
            db.session.commit()
            try:
                body = f"<p>Your password reset OTP is: <strong>{otp}</strong>. Valid for 10 minutes.</p>"
                mail_svc.send_email(email, 'Password Reset OTP', body)
            except Exception:
                pass
        flash('If that email is registered, an OTP has been sent.', 'info')
        return redirect(url_for('auth.verify_otp', email=email))

    return render_template('forgot_password.html')


@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    email = request.args.get('email', '')

    if request.method == 'POST':
        email = request.form.get('email', '')
        otp = request.form.get('otp', '').strip()
        new_password = request.form.get('new_password', '')

        user = User.query.filter_by(user_email=email).first()
        if not user:
            flash('Invalid request.', 'danger')
            return redirect(url_for('auth.login'))

        expiry = user.send_time + timedelta(minutes=user.max_validate_time or 10) if user.send_time else None
        if not expiry or datetime.utcnow() > expiry:
            flash('OTP has expired. Please request a new one.', 'danger')
            return redirect(url_for('auth.forgot_password'))

        if str(user.send_opt) != otp:
            flash('Invalid OTP.', 'danger')
            return render_template('verify_otp.html', email=email)

        if len(new_password) < 8:
            flash('Password must be at least 8 characters.', 'danger')
            return render_template('verify_otp.html', email=email)

        user.user_password = generate_password_hash(new_password, method='pbkdf2:sha256').encode()
        user.send_opt = None
        user.send_time = None
        db.session.commit()
        flash('Password reset successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('verify_otp.html', email=email)


@auth_bp.route('/auth/google/callback')
def google_callback():
    code = request.args.get('code')
    if not code:
        flash('Google authentication failed.', 'danger')
        return redirect(url_for('auth.login'))

    try:
        token_data = exchange_code(code)
        access_token = token_data.get('access_token')
        if not access_token:
            raise ValueError('No access token received.')

        user_info = get_user_info(access_token)
        google_email = user_info.get('email', '').lower()
        google_name = user_info.get('name', '')

        user = User.query.filter_by(user_email=google_email).first()
        if not user:
            # Auto-register as employee
            user = User(
                user_email=google_email,
                user_password=generate_password_hash(secrets.token_hex(16)).encode(),
                full_name=google_name,
                Birthday=datetime(1990, 1, 1).date(),
                male_female='Not Specified',
                user_type='employee',
                mobile_number=f"google_{secrets.token_hex(6)}",
                WhatsApp_number=f"google_{secrets.token_hex(6)}",
                user_active=1,
                user_block=0,
            )
            db.session.add(user)
            db.session.flush()
            profile = EmployeeProfileSeeker(
                link_to_user=user.id,
                employee_full_name=google_name,
            )
            db.session.add(profile)
            db.session.commit()

        if user.user_block:
            flash('This account has been suspended.', 'danger')
            return redirect(url_for('auth.login'))

        session.clear()
        session['user_id'] = user.id
        session['user_type'] = user.user_type.strip()
        session['full_name'] = user.full_name
        session['last_login'] = int(datetime.utcnow().timestamp())
        session['is_paper_admin'] = int(user.is_paper_admin or 0)

        role = user.user_type.strip().lower()
        dest = ROLE_REDIRECT.get(role, 'main.index')
        return redirect(url_for(dest))

    except Exception as e:
        logging.error(f"Google callback error: {e}")
        flash('Google authentication failed. Please try again.', 'danger')
        return redirect(url_for('auth.login'))
