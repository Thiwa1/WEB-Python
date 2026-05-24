from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash, jsonify, current_app, send_file)
from sqlalchemy import func
from database import db
from models import (AdvertisingTable, EmployeeProfileSeeker, JobApplication,
                    EmployeeAlertSetting, EmployeeDocument, TalentOffer,
                    District, City, JobCategory, User)
from services import upload as upload_svc
from routes.auth import login_required, role_required
from services.ai_recruiter import AiRecruiter
from datetime import date
import io

employee_bp = Blueprint('employee', __name__, url_prefix='/employee')

ai = AiRecruiter()


def get_seeker_profile():
    return EmployeeProfileSeeker.query.filter_by(link_to_user=session['user_id']).first_or_404()


@employee_bp.route('/dashboard')
@login_required
@role_required('employee', 'seeker', 'candidate')
def dashboard():
    profile = get_seeker_profile()
    applications = (db.session.query(JobApplication, AdvertisingTable)
                    .join(AdvertisingTable, JobApplication.job_ad_link == AdvertisingTable.id)
                    .filter(JobApplication.seeker_link == profile.id)
                    .order_by(JobApplication.applied_date.desc())
                    .limit(5).all())

    active_jobs_count = (AdvertisingTable.query
                         .filter(AdvertisingTable.Approved == 1,
                                 AdvertisingTable.Closing_date >= date.today())
                         .count())

    talent_offer = TalentOffer.query.filter_by(seeker_link=profile.id, is_active=1).first()

    return render_template('employee/dashboard.html',
                           profile=profile, applications=applications,
                           active_jobs_count=active_jobs_count, talent_offer=talent_offer)


@employee_bp.route('/browse-jobs')
@login_required
@role_required('employee', 'seeker', 'candidate')
def browse_jobs():
    districts = District.query.order_by(District.District_name).all()
    categories = JobCategory.query.order_by(JobCategory.Description).all()

    keyword = request.args.get('keyword', '')
    district = request.args.get('district', '')
    category = request.args.get('category', '')
    job_type = request.args.get('job_type', '')

    query = AdvertisingTable.query.filter(
        AdvertisingTable.Approved == 1,
        AdvertisingTable.Closing_date >= date.today()
    )
    if keyword:
        query = query.filter(AdvertisingTable.Job_role.ilike(f'%{keyword}%'))
    if district:
        query = query.filter(AdvertisingTable.District == district)
    if category:
        query = query.filter(AdvertisingTable.Job_category == category)
    if job_type:
        query = query.filter(AdvertisingTable.job_type == job_type)

    jobs = query.order_by(AdvertisingTable.id.desc()).all()
    return render_template('employee/browse_jobs.html',
                           jobs=jobs, districts=districts, categories=categories,
                           keyword=keyword, district=district, category=category, job_type=job_type)


@employee_bp.route('/apply/<int:job_id>', methods=['GET', 'POST'])
@login_required
@role_required('employee', 'seeker', 'candidate')
def apply_job(job_id):
    profile = get_seeker_profile()
    job = AdvertisingTable.query.get_or_404(job_id)

    if request.method == 'POST':
        existing = JobApplication.query.filter_by(
            job_ad_link=job_id, seeker_link=profile.id).first()
        if existing:
            flash('You have already applied for this job.', 'warning')
            return redirect(url_for('employee.my_applications'))

        app_entry = JobApplication(job_ad_link=job_id, seeker_link=profile.id)
        db.session.add(app_entry)
        db.session.commit()
        flash('Application submitted!', 'success')
        return redirect(url_for('employee.my_applications'))

    return render_template('employee/apply_confirm.html', job=job, profile=profile)


@employee_bp.route('/my-applications')
@login_required
@role_required('employee', 'seeker', 'candidate')
def my_applications():
    profile = get_seeker_profile()
    applications = (db.session.query(JobApplication, AdvertisingTable)
                    .join(AdvertisingTable, JobApplication.job_ad_link == AdvertisingTable.id)
                    .filter(JobApplication.seeker_link == profile.id)
                    .order_by(JobApplication.applied_date.desc())
                    .all())
    return render_template('employee/my_applications.html',
                           profile=profile, applications=applications)


@employee_bp.route('/edit-profile', methods=['GET', 'POST'])
@login_required
@role_required('employee', 'seeker', 'candidate')
def edit_profile():
    profile = get_seeker_profile()
    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        profile.employee_full_name = request.form.get('full_name', '').strip()
        profile.employee_name_with_initial = request.form.get('name_with_initial', '').strip()
        user.mobile_number = request.form.get('mobile_number', user.mobile_number).strip()
        user.WhatsApp_number = request.form.get('whatsapp_number', user.WhatsApp_number).strip()

        img_file = request.files.get('profile_img')
        if img_file and img_file.filename:
            profile.img_path = upload_svc.save_file(img_file, 'profile_imgs',
                                                    current_app.config['ALLOWED_IMAGE_EXTENSIONS'])

        cv_file = request.files.get('cv')
        if cv_file and cv_file.filename:
            profile.cv_path = upload_svc.save_file(cv_file, 'cvs',
                                                   current_app.config['ALLOWED_DOC_EXTENSIONS'])

        cl_file = request.files.get('cover_letter')
        if cl_file and cl_file.filename:
            profile.cl_path = upload_svc.save_file(cl_file, 'cl',
                                                   current_app.config['ALLOWED_DOC_EXTENSIONS'])

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('employee.edit_profile'))

    return render_template('employee/edit_profile.html', profile=profile, user=user)


@employee_bp.route('/manage-documents', methods=['GET', 'POST'])
@login_required
@role_required('employee', 'seeker', 'candidate')
def manage_documents():
    profile = get_seeker_profile()
    documents = EmployeeDocument.query.filter_by(link_to_employee_profile=profile.id).all()

    if request.method == 'POST':
        doc_type = request.form.get('document_type', '').strip()
        doc_file = request.files.get('document')
        if doc_file and doc_file.filename and doc_type:
            doc_path = upload_svc.save_file(doc_file, 'documents',
                                            current_app.config['ALLOWED_DOC_EXTENSIONS'])
            doc = EmployeeDocument(
                link_to_employee_profile=profile.id,
                document_type=doc_type,
                doc_path=doc_path,
            )
            db.session.add(doc)
            db.session.commit()
            flash('Document uploaded.', 'success')
        else:
            flash('Document type and file are required.', 'danger')
        return redirect(url_for('employee.manage_documents'))

    return render_template('employee/manage_documents.html', profile=profile, documents=documents)


@employee_bp.route('/delete-document/<int:doc_id>', methods=['POST'])
@login_required
@role_required('employee', 'seeker', 'candidate')
def delete_document(doc_id):
    profile = get_seeker_profile()
    doc = EmployeeDocument.query.filter_by(id=doc_id, link_to_employee_profile=profile.id).first_or_404()
    upload_svc.delete_file(doc.doc_path)
    db.session.delete(doc)
    db.session.commit()
    flash('Document deleted.', 'success')
    return redirect(url_for('employee.manage_documents'))


@employee_bp.route('/alert-settings', methods=['GET', 'POST'])
@login_required
@role_required('employee', 'seeker', 'candidate')
def alert_settings():
    profile = get_seeker_profile()
    alerts = EmployeeAlertSetting.query.filter_by(link_to_employee_profile=profile.id).all()
    districts = District.query.order_by(District.District_name).all()
    categories = JobCategory.query.order_by(JobCategory.Description).all()

    if request.method == 'POST':
        district = request.form.get('district', '')
        city = request.form.get('city', '')
        category = request.form.get('job_category', '')

        alert = EmployeeAlertSetting(
            district=district,
            city=city,
            job_category=category,
            link_to_employee_profile=profile.id,
            active=1,
        )
        db.session.add(alert)
        db.session.commit()
        flash('Alert added!', 'success')
        return redirect(url_for('employee.alert_settings'))

    return render_template('employee/alert_settings.html',
                           profile=profile, alerts=alerts,
                           districts=districts, categories=categories)


@employee_bp.route('/delete-alert/<int:alert_id>', methods=['POST'])
@login_required
@role_required('employee', 'seeker', 'candidate')
def delete_alert(alert_id):
    profile = get_seeker_profile()
    alert = EmployeeAlertSetting.query.filter_by(
        id=alert_id, link_to_employee_profile=profile.id).first_or_404()
    db.session.delete(alert)
    db.session.commit()
    flash('Alert removed.', 'success')
    return redirect(url_for('employee.alert_settings'))


@employee_bp.route('/promote-self', methods=['GET', 'POST'])
@login_required
@role_required('employee', 'seeker', 'candidate')
def promote_self():
    profile = get_seeker_profile()
    offer = TalentOffer.query.filter_by(seeker_link=profile.id).first()

    if request.method == 'POST':
        headline = request.form.get('headline', '').strip()
        skills = request.form.get('skills_tags', '')
        exp_years = int(request.form.get('experience_years', 0) or 0)
        salary = float(request.form.get('expected_salary', 0) or 0)
        description = request.form.get('description', '')
        expiry = request.form.get('expiry_date', '')

        if not headline or not expiry:
            flash('Headline and expiry date are required.', 'danger')
            return render_template('employee/promote_self.html', profile=profile, offer=offer)

        if offer:
            offer.headline = headline
            offer.skills_tags = skills
            offer.experience_years = exp_years
            offer.expected_salary = salary
            offer.description = description
            offer.expiry_date = expiry
            offer.is_active = 1
        else:
            offer = TalentOffer(
                seeker_link=profile.id,
                headline=headline,
                skills_tags=skills,
                experience_years=exp_years,
                expected_salary=salary,
                description=description,
                expiry_date=expiry,
            )
            db.session.add(offer)

        db.session.commit()
        flash('Your talent profile is now live!', 'success')
        return redirect(url_for('employee.dashboard'))

    return render_template('employee/promote_self.html', profile=profile, offer=offer)


@employee_bp.route('/score-cv', methods=['POST'])
@login_required
def score_cv():
    data = request.get_json()
    cv_text = data.get('cv_text', '')
    job_desc = data.get('job_description', '')
    candidate_exp = int(data.get('candidate_exp', 0) or 0)
    required_exp = int(data.get('required_exp', 0) or 0)

    result = ai.score_cv(cv_text, job_desc, candidate_exp, required_exp)
    return jsonify(result)
