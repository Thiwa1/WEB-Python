from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash, jsonify, current_app, send_file)
from werkzeug.security import generate_password_hash
from sqlalchemy import func
from database import db
from models import (AdvertisingTable, EmployerProfile, JobApplication,
                    GuestJobApplication, PaymentTable, PaidAdvertising,
                    District, City, JobCategory, IndustrySetting,
                    SiteSetting, SystemBankAccount, PriceSetting,
                    TalentOffer, EmployeeProfileSeeker, User, PaperAd)
from services import upload as upload_svc
from routes.auth import login_required, role_required
from datetime import date
import io

employer_bp = Blueprint('employer', __name__, url_prefix='/employer')


def get_employer_profile():
    return EmployerProfile.query.filter_by(link_to_user=session['user_id']).first_or_404()


@employer_bp.route('/dashboard')
@login_required
@role_required('employer')
def dashboard():
    profile = get_employer_profile()
    jobs = AdvertisingTable.query.filter_by(
        link_to_employer_profile=profile.id
    ).order_by(AdvertisingTable.id.desc()).all()

    stats = {
        'total_jobs': len(jobs),
        'active_jobs': sum(1 for j in jobs if j.Closing_date and j.Closing_date >= date.today() and j.Approved),
        'pending_approval': sum(1 for j in jobs if not j.Approved),
        'total_applications': db.session.query(func.count(JobApplication.id))
            .join(AdvertisingTable, JobApplication.job_ad_link == AdvertisingTable.id)
            .filter(AdvertisingTable.link_to_employer_profile == profile.id)
            .scalar() or 0,
    }
    return render_template('employer/dashboard.html', profile=profile, jobs=jobs, stats=stats)


@employer_bp.route('/post-job', methods=['GET', 'POST'])
@login_required
@role_required('employer')
def post_job():
    profile = get_employer_profile()

    districts = District.query.order_by(District.District_name).all()
    categories = JobCategory.query.order_by(JobCategory.Description).all()
    industries = IndustrySetting.query.order_by(IndustrySetting.Industry_name).all()
    banks = SystemBankAccount.query.all()
    price_settings = PriceSetting.query.all()

    promo_setting = SiteSetting.query.filter_by(setting_key='promo_active').first()
    is_promo = promo_setting and promo_setting.setting_value == '1'

    if request.method == 'POST':
        try:
            job_role = request.form.get('Job_role', '').strip()
            job_type = request.form.get('job_type', 'Full Time')
            job_category = request.form.get('Job_category', '')
            industry = request.form.get('Industry', '')
            opening_date = request.form.get('Opening_date')
            closing_date = request.form.get('Closing_date')
            district = request.form.get('District', '')
            city = request.form.get('City', '')
            job_desc = request.form.get('job_description', '')
            apply_email = int(request.form.get('Apply_by_email', 0))
            apply_system = int(request.form.get('Apply_by_system', 1))
            apply_whatsapp = int(request.form.get('apply_WhatsApp', 0))
            email_addr = request.form.get('Apply_by_email_address', '')
            whatsapp_no = request.form.get('apply_WhatsApp_No', '')

            if not job_role or not closing_date:
                raise ValueError('Job title and closing date are required.')

            img_path = None
            img_file = request.files.get('Img')
            if img_file and img_file.filename:
                img_path = upload_svc.save_file(img_file, 'job_images',
                                                current_app.config['ALLOWED_IMAGE_EXTENSIONS'])

            slip_path = None
            if not is_promo:
                slip_file = request.files.get('payment_slip')
                if slip_file and slip_file.filename:
                    slip_path = upload_svc.save_file(slip_file, 'slips',
                                                     current_app.config['ALLOWED_IMAGE_EXTENSIONS'] | {'pdf'})

            job = AdvertisingTable(
                link_to_employer_profile=profile.id,
                Job_role=job_role,
                job_type=job_type,
                Job_category=job_category,
                Industry=industry,
                Opening_date=opening_date or date.today(),
                Closing_date=closing_date,
                District=district,
                City=city,
                job_description=job_desc,
                Apply_by_email=apply_email,
                Apply_by_system=apply_system,
                apply_WhatsApp=apply_whatsapp,
                Apply_by_email_address=email_addr,
                apply_WhatsApp_No=whatsapp_no,
                img_path=img_path,
                Approved=0,
            )
            db.session.add(job)
            db.session.flush()

            if not is_promo and slip_path:
                amount = float(request.form.get('total_amount', 0) or 0)
                payment = PaymentTable(
                    employer_link=profile.id,
                    Totaled_received=amount,
                    payment_date=date.today(),
                    slip_path=slip_path,
                )
                db.session.add(payment)
                db.session.flush()
                paid = PaidAdvertising(slip_link=payment.id, add_link=job.id)
                db.session.add(paid)

            db.session.commit()
            flash('Job posted successfully! It will be reviewed before going live.', 'success')
            return redirect(url_for('employer.manage_jobs'))

        except ValueError as e:
            db.session.rollback()
            flash(str(e), 'danger')
        except Exception as e:
            db.session.rollback()
            import logging
            logging.error(f"Post job error: {e}")
            flash('An error occurred. Please try again.', 'danger')

    return render_template('employer/post_job.html',
                           profile=profile, districts=districts, categories=categories,
                           industries=industries, banks=banks, price_settings=price_settings,
                           is_promo=is_promo)


@employer_bp.route('/manage-jobs')
@login_required
@role_required('employer')
def manage_jobs():
    profile = get_employer_profile()
    jobs = AdvertisingTable.query.filter_by(
        link_to_employer_profile=profile.id
    ).order_by(AdvertisingTable.id.desc()).all()
    return render_template('employer/manage_jobs.html', profile=profile, jobs=jobs)


@employer_bp.route('/edit-job/<int:job_id>', methods=['GET', 'POST'])
@login_required
@role_required('employer')
def edit_job(job_id):
    profile = get_employer_profile()
    job = AdvertisingTable.query.filter_by(id=job_id, link_to_employer_profile=profile.id).first_or_404()

    districts = District.query.order_by(District.District_name).all()
    categories = JobCategory.query.order_by(JobCategory.Description).all()
    industries = IndustrySetting.query.order_by(IndustrySetting.Industry_name).all()

    if request.method == 'POST':
        job.Job_role = request.form.get('Job_role', job.Job_role).strip()
        job.job_type = request.form.get('job_type', job.job_type)
        job.Job_category = request.form.get('Job_category', job.Job_category)
        job.Industry = request.form.get('Industry', job.Industry)
        job.Closing_date = request.form.get('Closing_date', str(job.Closing_date))
        job.District = request.form.get('District', job.District)
        job.City = request.form.get('City', job.City)
        job.job_description = request.form.get('job_description', job.job_description)
        job.Apply_by_email = int(request.form.get('Apply_by_email', 0))
        job.Apply_by_system = int(request.form.get('Apply_by_system', 1))
        job.apply_WhatsApp = int(request.form.get('apply_WhatsApp', 0))
        job.Apply_by_email_address = request.form.get('Apply_by_email_address', '')
        job.apply_WhatsApp_No = request.form.get('apply_WhatsApp_No', '')
        job.Approved = 0  # re-review on edit

        img_file = request.files.get('Img')
        if img_file and img_file.filename:
            job.img_path = upload_svc.save_file(img_file, 'job_images',
                                                current_app.config['ALLOWED_IMAGE_EXTENSIONS'])

        db.session.commit()
        flash('Job updated. It will be re-reviewed before going live.', 'success')
        return redirect(url_for('employer.manage_jobs'))

    return render_template('employer/edit_job.html', job=job, districts=districts,
                           categories=categories, industries=industries)


@employer_bp.route('/delete-job/<int:job_id>', methods=['POST'])
@login_required
@role_required('employer')
def delete_job(job_id):
    profile = get_employer_profile()
    job = AdvertisingTable.query.filter_by(id=job_id, link_to_employer_profile=profile.id).first_or_404()
    db.session.delete(job)
    db.session.commit()
    flash('Job deleted.', 'success')
    return redirect(url_for('employer.manage_jobs'))


@employer_bp.route('/view-applications/<int:job_id>')
@login_required
@role_required('employer')
def view_applications(job_id):
    profile = get_employer_profile()
    job = AdvertisingTable.query.filter_by(id=job_id, link_to_employer_profile=profile.id).first_or_404()

    registered = (db.session.query(JobApplication, EmployeeProfileSeeker, User)
                  .join(EmployeeProfileSeeker, JobApplication.seeker_link == EmployeeProfileSeeker.id)
                  .join(User, EmployeeProfileSeeker.link_to_user == User.id)
                  .filter(JobApplication.job_ad_link == job_id)
                  .all())
    guests = GuestJobApplication.query.filter_by(job_ad_link=job_id).all()

    return render_template('employer/view_applications.html',
                           job=job, registered=registered, guests=guests)


@employer_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@role_required('employer')
def profile():
    prof = get_employer_profile()

    if request.method == 'POST':
        prof.employer_name = request.form.get('employer_name', prof.employer_name).strip()
        prof.employer_address_1 = request.form.get('employer_address_1', '')
        prof.employer_address_2 = request.form.get('employer_address_2', '')
        prof.employer_address_3 = request.form.get('employer_address_3', '')
        prof.employer_mobile_no = request.form.get('employer_mobile_no', '')
        prof.employer_whatsapp_no = request.form.get('employer_whatsapp_no', '')
        prof.employer_about_company = request.form.get('employer_about_company', '')

        logo_file = request.files.get('employer_logo')
        if logo_file and logo_file.filename:
            prof.logo_path = upload_svc.save_file(logo_file, 'logos',
                                                  current_app.config['ALLOWED_IMAGE_EXTENSIONS'])
        br_file = request.files.get('employer_BR')
        if br_file and br_file.filename:
            prof.br_path = upload_svc.save_file(br_file, 'br',
                                                current_app.config['ALLOWED_DOC_EXTENSIONS'])

        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('employer.profile'))

    return render_template('employer/profile.html', profile=prof)


@employer_bp.route('/billing')
@login_required
@role_required('employer')
def billing():
    profile = get_employer_profile()
    payments = PaymentTable.query.filter_by(employer_link=profile.id).order_by(PaymentTable.id.desc()).all()
    banks = SystemBankAccount.query.all()
    return render_template('employer/billing.html', profile=profile, payments=payments, banks=banks)


@employer_bp.route('/payment-history')
@login_required
@role_required('employer')
def payment_history():
    profile = get_employer_profile()
    payments = (db.session.query(PaymentTable, PaidAdvertising, AdvertisingTable)
                .outerjoin(PaidAdvertising, PaymentTable.id == PaidAdvertising.slip_link)
                .outerjoin(AdvertisingTable, PaidAdvertising.add_link == AdvertisingTable.id)
                .filter(PaymentTable.employer_link == profile.id)
                .order_by(PaymentTable.id.desc())
                .all())
    return render_template('employer/payment_history.html', profile=profile, payments=payments)


@employer_bp.route('/reupload-payment/<int:payment_id>', methods=['GET', 'POST'])
@login_required
@role_required('employer')
def reupload_payment(payment_id):
    profile = get_employer_profile()
    payment = PaymentTable.query.filter_by(id=payment_id, employer_link=profile.id).first_or_404()

    if request.method == 'POST':
        slip_file = request.files.get('payment_slip')
        if slip_file and slip_file.filename:
            payment.slip_path = upload_svc.save_file(slip_file, 'slips',
                                                     current_app.config['ALLOWED_IMAGE_EXTENSIONS'] | {'pdf'})
            payment.Approval = 0
            db.session.commit()
            flash('Payment slip re-uploaded. Awaiting approval.', 'success')
            return redirect(url_for('employer.billing'))
        flash('No file selected.', 'danger')

    return render_template('employer/reupload_payment.html', payment=payment)


@employer_bp.route('/bank-details', methods=['GET', 'POST'])
@login_required
@role_required('employer')
def bank_details():
    profile = get_employer_profile()
    banks = SystemBankAccount.query.all()
    return render_template('employer/bank_details.html', profile=profile, banks=banks)


@employer_bp.route('/talent-pool')
@login_required
@role_required('employer')
def talent_pool():
    offers = (db.session.query(TalentOffer, EmployeeProfileSeeker, User)
              .join(EmployeeProfileSeeker, TalentOffer.seeker_link == EmployeeProfileSeeker.id)
              .join(User, EmployeeProfileSeeker.link_to_user == User.id)
              .filter(TalentOffer.is_active == 1,
                      TalentOffer.expiry_date >= date.today())
              .order_by(TalentOffer.created_at.desc())
              .all())
    return render_template('employer/talent_pool.html', offers=offers)


@employer_bp.route('/application-status/<int:app_id>', methods=['POST'])
@login_required
@role_required('employer')
def update_application_status(app_id):
    profile = get_employer_profile()
    app_entry = JobApplication.query.get_or_404(app_id)
    job = AdvertisingTable.query.get(app_entry.job_ad_link)
    if not job or job.link_to_employer_profile != profile.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('employer.dashboard'))

    new_status = request.form.get('status', 'Pending')
    reason = request.form.get('rejection_reason', '')
    app_entry.application_status = new_status
    app_entry.rejection_reason = reason if new_status == 'Rejected' else None
    db.session.commit()
    flash(f'Application status updated to {new_status}.', 'success')
    return redirect(url_for('employer.view_applications', job_id=app_entry.job_ad_link))


@employer_bp.route('/promote-paper-ad', methods=['GET', 'POST'])
@login_required
@role_required('employer')
def submit_paper_ad():
    profile = get_employer_profile()
    banks = SystemBankAccount.query.all()

    if request.method == 'POST':
        ad_text = request.form.get('ad_text', '').strip()
        contact_info = request.form.get('contact_info', '').strip()
        slip_file = request.files.get('payment_slip')

        if not ad_text:
            flash('Ad text is required.', 'danger')
            return render_template('employer/paper_ad_form.html', banks=banks, profile=profile)

        slip_path = None
        if slip_file and slip_file.filename:
            slip_path = upload_svc.save_file(slip_file, 'slips',
                                             current_app.config['ALLOWED_IMAGE_EXTENSIONS'] | {'pdf'})

        ad = PaperAd(employer_link=profile.id, ad_text=ad_text,
                     contact_info=contact_info, slip_path=slip_path)
        db.session.add(ad)
        db.session.commit()
        flash('Paper ad submitted for review!', 'success')
        return redirect(url_for('employer.dashboard'))

    return render_template('employer/paper_ad_form.html', banks=banks, profile=profile)
