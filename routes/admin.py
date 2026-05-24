from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash, jsonify, current_app)
from sqlalchemy import func
from database import db
from models import (AdvertisingTable, EmployerProfile, EmployeeProfileSeeker,
                    User, PaymentTable, PaidAdvertising, SiteSetting,
                    SystemBankAccount, PriceSetting, CompanyDetails,
                    JobCategory, District, IndustrySetting, PaperAd, SmsLog)
from services.sms import send_sms
from services.mail import send_email
from routes.auth import login_required, role_required
from datetime import date

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    stats = {
        'total_jobs': AdvertisingTable.query.count(),
        'pending_jobs': AdvertisingTable.query.filter_by(Approved=0).count(),
        'total_employers': EmployerProfile.query.count(),
        'total_seekers': EmployeeProfileSeeker.query.count(),
        'pending_payments': PaymentTable.query.filter_by(Approval=0).count(),
        'active_jobs': AdvertisingTable.query.filter(
            AdvertisingTable.Approved == 1,
            AdvertisingTable.Closing_date >= date.today()
        ).count(),
    }
    recent_jobs = AdvertisingTable.query.order_by(AdvertisingTable.id.desc()).limit(10).all()
    return render_template('admin/dashboard.html', stats=stats, recent_jobs=recent_jobs)


@admin_bp.route('/manage-jobs')
@login_required
@role_required('admin')
def manage_jobs():
    jobs = (db.session.query(AdvertisingTable, EmployerProfile)
            .join(EmployerProfile, AdvertisingTable.link_to_employer_profile == EmployerProfile.id)
            .order_by(AdvertisingTable.id.desc())
            .all())
    return render_template('admin/manage_jobs.html', jobs=jobs)


@admin_bp.route('/approve-job/<int:job_id>', methods=['POST'])
@login_required
@role_required('admin')
def approve_job(job_id):
    job = AdvertisingTable.query.get_or_404(job_id)
    job.Approved = 1
    job.Rejection_comment = None
    job.rejection_reason = None
    db.session.commit()

    # SMS alert to matching subscribers
    try:
        from models import EmployeeAlertSetting
        alerts = EmployeeAlertSetting.query.filter(
            (EmployeeAlertSetting.district == job.District) |
            (EmployeeAlertSetting.job_category == job.Job_category),
            EmployeeAlertSetting.active == 1
        ).all()
        for alert in alerts:
            seeker = EmployeeProfileSeeker.query.get(alert.link_to_employee_profile)
            if seeker:
                user = User.query.get(seeker.link_to_user)
                if user:
                    msg = f"New job alert: {job.Job_role} in {job.District}. Visit our portal to apply."
                    send_sms(user.mobile_number, msg)
                    log = SmsLog(job_id=job.id, user_id=user.id,
                                 phone_number=user.mobile_number)
                    db.session.add(log)
        db.session.commit()
    except Exception as e:
        import logging
        logging.error(f"SMS alert error: {e}")

    flash('Job approved and subscribers notified.', 'success')
    return redirect(url_for('admin.manage_jobs'))


@admin_bp.route('/reject-job/<int:job_id>', methods=['POST'])
@login_required
@role_required('admin')
def reject_job(job_id):
    job = AdvertisingTable.query.get_or_404(job_id)
    reason = request.form.get('rejection_reason', '')
    job.Approved = 0
    job.rejection_reason = reason
    db.session.commit()
    flash('Job rejected.', 'warning')
    return redirect(url_for('admin.manage_jobs'))


@admin_bp.route('/delete-job/<int:job_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_job(job_id):
    job = AdvertisingTable.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    flash('Job deleted.', 'success')
    return redirect(url_for('admin.manage_jobs'))


@admin_bp.route('/approve-payments')
@login_required
@role_required('admin')
def approve_payments():
    payments = (db.session.query(PaymentTable, EmployerProfile, User)
                .join(EmployerProfile, PaymentTable.employer_link == EmployerProfile.id)
                .join(User, EmployerProfile.link_to_user == User.id)
                .order_by(PaymentTable.id.desc())
                .all())
    return render_template('admin/approve_payments.html', payments=payments)


@admin_bp.route('/approve-payment/<int:payment_id>', methods=['POST'])
@login_required
@role_required('admin')
def approve_payment(payment_id):
    payment = PaymentTable.query.get_or_404(payment_id)
    payment.Approval = 1
    payment.Approval_date = date.today()
    db.session.commit()
    flash('Payment approved.', 'success')
    return redirect(url_for('admin.approve_payments'))


@admin_bp.route('/reject-payment/<int:payment_id>', methods=['POST'])
@login_required
@role_required('admin')
def reject_payment(payment_id):
    payment = PaymentTable.query.get_or_404(payment_id)
    payment.Approval = 2
    payment.Reject_comment = request.form.get('reject_comment', '')
    db.session.commit()
    flash('Payment rejected.', 'warning')
    return redirect(url_for('admin.approve_payments'))


@admin_bp.route('/verify-recruiters')
@login_required
@role_required('admin')
def verify_recruiters():
    employers = (db.session.query(EmployerProfile, User)
                 .join(User, EmployerProfile.link_to_user == User.id)
                 .order_by(EmployerProfile.employer_Verified.asc(), EmployerProfile.id.desc())
                 .all())
    return render_template('admin/verify_recruiters.html', employers=employers)


@admin_bp.route('/verify-employer/<int:emp_id>', methods=['POST'])
@login_required
@role_required('admin')
def verify_employer(emp_id):
    emp = EmployerProfile.query.get_or_404(emp_id)
    emp.employer_Verified = 1
    emp.employer_Verified_by = session.get('full_name', 'Admin')
    db.session.commit()
    flash('Employer verified.', 'success')
    return redirect(url_for('admin.verify_recruiters'))


@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def settings():
    if request.method == 'POST':
        for key in ('promo_active', 'admin_email', 'vat_rate', 'site_name'):
            val = request.form.get(key, '')
            setting = SiteSetting.query.filter_by(setting_key=key).first()
            if setting:
                setting.setting_value = val
            else:
                db.session.add(SiteSetting(setting_key=key, setting_value=val))
        db.session.commit()
        flash('Settings saved.', 'success')
        return redirect(url_for('admin.settings'))

    all_settings = {s.setting_key: s.setting_value for s in SiteSetting.query.all()}
    return render_template('admin/settings.html', settings=all_settings)


@admin_bp.route('/bank-accounts', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def bank_accounts():
    if request.method == 'POST':
        bank = SystemBankAccount(
            bank_name=request.form.get('bank_name', ''),
            account_number=request.form.get('account_number', ''),
            branch_name=request.form.get('branch_name', ''),
            branch_code=request.form.get('branch_code', ''),
        )
        db.session.add(bank)
        db.session.commit()
        flash('Bank account added.', 'success')
        return redirect(url_for('admin.bank_accounts'))

    banks = SystemBankAccount.query.all()
    return render_template('admin/bank_accounts.html', banks=banks)


@admin_bp.route('/delete-bank/<int:bank_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_bank(bank_id):
    bank = SystemBankAccount.query.get_or_404(bank_id)
    db.session.delete(bank)
    db.session.commit()
    flash('Bank account removed.', 'success')
    return redirect(url_for('admin.bank_accounts'))


@admin_bp.route('/manage-rates', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def manage_rates():
    if request.method == 'POST':
        units = int(request.form.get('units', 0) or 0)
        price = float(request.form.get('price', 0) or 0)
        setting = PriceSetting(Unit_of_add=units, selling_price=price)
        db.session.add(setting)
        db.session.commit()
        flash('Rate added.', 'success')
        return redirect(url_for('admin.manage_rates'))

    rates = PriceSetting.query.all()
    return render_template('admin/manage_rates.html', rates=rates)


@admin_bp.route('/sms-panel', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def sms_panel():
    if request.method == 'POST':
        phone = request.form.get('phone_number', '').strip()
        message = request.form.get('message', '').strip()
        if phone and message:
            success = send_sms(phone, message)
            flash('SMS sent!' if success else 'SMS failed. Check configuration.', 'success' if success else 'danger')
        else:
            flash('Phone and message are required.', 'danger')

    logs = SmsLog.query.order_by(SmsLog.sent_at.desc()).limit(50).all()
    return render_template('admin/sms_panel.html', logs=logs)


@admin_bp.route('/revenue-report')
@login_required
@role_required('admin')
def revenue_report():
    payments = (db.session.query(PaymentTable, EmployerProfile, User)
                .join(EmployerProfile, PaymentTable.employer_link == EmployerProfile.id)
                .join(User, EmployerProfile.link_to_user == User.id)
                .filter(PaymentTable.Approval == 1)
                .order_by(PaymentTable.Approval_date.desc())
                .all())
    total = sum(p.PaymentTable.Totaled_received for p in payments) if payments else 0
    return render_template('admin/revenue_report.html', payments=payments, total=total)


@admin_bp.route('/seeker-report')
@login_required
@role_required('admin')
def seeker_report():
    seekers = (db.session.query(EmployeeProfileSeeker, User)
               .join(User, EmployeeProfileSeeker.link_to_user == User.id)
               .order_by(User.created_at.desc())
               .all())
    return render_template('admin/seeker_report.html', seekers=seekers)


@admin_bp.route('/manage-paper-ads')
@login_required
@role_required('admin', 'paperadmin')
def paper_ads():
    ads = (db.session.query(PaperAd, EmployerProfile, User)
           .join(EmployerProfile, PaperAd.employer_link == EmployerProfile.id)
           .join(User, EmployerProfile.link_to_user == User.id)
           .order_by(PaperAd.submitted_at.desc())
           .all())
    return render_template('admin/manage_paper_ads.html', ads=ads)


@admin_bp.route('/approve-paper-ad/<int:ad_id>', methods=['POST'])
@login_required
@role_required('admin', 'paperadmin')
def approve_paper_ad(ad_id):
    from datetime import datetime
    ad = PaperAd.query.get_or_404(ad_id)
    ad.status = 'Approved'
    ad.approved_at = datetime.utcnow()
    db.session.commit()
    flash('Paper ad approved.', 'success')
    return redirect(url_for('admin.paper_ads'))


@admin_bp.route('/reject-paper-ad/<int:ad_id>', methods=['POST'])
@login_required
@role_required('admin', 'paperadmin')
def reject_paper_ad(ad_id):
    ad = PaperAd.query.get_or_404(ad_id)
    ad.status = 'Rejected'
    db.session.commit()
    flash('Paper ad rejected.', 'warning')
    return redirect(url_for('admin.paper_ads'))


@admin_bp.route('/manage-staff')
@login_required
@role_required('admin')
def manage_staff():
    staff = User.query.filter(User.user_type.in_(['admin', 'paperadmin'])).all()
    return render_template('admin/manage_staff.html', staff=staff)


@admin_bp.route('/manage-categories', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def manage_categories():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add_category':
            desc = request.form.get('description', '').strip()
            if desc:
                db.session.add(JobCategory(Description=desc))
                db.session.commit()
                flash('Category added.', 'success')
        elif action == 'add_district':
            name = request.form.get('district_name', '').strip()
            if name:
                db.session.add(District(District_name=name))
                db.session.commit()
                flash('District added.', 'success')
        return redirect(url_for('admin.manage_categories'))

    categories = JobCategory.query.order_by(JobCategory.Description).all()
    districts = District.query.order_by(District.District_name).all()
    industries = IndustrySetting.query.order_by(IndustrySetting.Industry_name).all()
    return render_template('admin/manage_categories.html',
                           categories=categories, districts=districts, industries=industries)
