from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash, jsonify, current_app)
from sqlalchemy import func, text
from database import db
from models import (AdvertisingTable, District, City, JobCategory,
                    EmployerProfile, EmployeeProfileSeeker, JobViewsLog,
                    GuestJobApplication, SiteSetting)
from services import upload as upload_svc
from datetime import date

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    districts = District.query.order_by(District.District_name).all()
    categories = JobCategory.query.order_by(JobCategory.Description).all()

    job_type_counts = {
        jt: db.session.query(func.count(AdvertisingTable.id))
               .filter(AdvertisingTable.job_type == jt,
                       AdvertisingTable.Approved == 1,
                       AdvertisingTable.Closing_date >= date.today())
               .scalar() or 0
        for jt in ('Full Time', 'Part Time', 'Online', 'School Leaver')
    }

    total_seekers = EmployeeProfileSeeker.query.count()
    total_employers = EmployerProfile.query.count()
    total_views = db.session.query(func.count(JobViewsLog.id)).scalar() or 0

    keyword = request.args.get('keyword', '')
    district_filter = request.args.get('district', '')
    city_filter = request.args.get('city', '')
    category_filter = request.args.get('category', '')
    job_type_filter = request.args.get('job_type', '')

    query = (AdvertisingTable.query
             .join(EmployerProfile, AdvertisingTable.link_to_employer_profile == EmployerProfile.id)
             .filter(AdvertisingTable.Approved == 1,
                     AdvertisingTable.Closing_date >= date.today()))

    if keyword:
        query = query.filter(
            AdvertisingTable.Job_role.ilike(f'%{keyword}%') |
            AdvertisingTable.job_description.ilike(f'%{keyword}%')
        )
    if district_filter:
        query = query.filter(AdvertisingTable.District == district_filter)
    if city_filter:
        query = query.filter(AdvertisingTable.City == city_filter)
    if category_filter:
        query = query.filter(AdvertisingTable.Job_category == category_filter)
    if job_type_filter:
        query = query.filter(AdvertisingTable.job_type == job_type_filter)

    jobs = query.order_by(AdvertisingTable.id.desc()).limit(50).all()

    return render_template('index.html',
                           districts=districts, categories=categories,
                           jobs=jobs, job_type_counts=job_type_counts,
                           total_seekers=total_seekers, total_employers=total_employers,
                           total_views=total_views,
                           keyword=keyword, district_filter=district_filter,
                           city_filter=city_filter, category_filter=category_filter,
                           job_type_filter=job_type_filter)


@main_bp.route('/jobs')
def job_view():
    return redirect(url_for('main.index'))


@main_bp.route('/job/<int:job_id>')
def job_details(job_id):
    job = AdvertisingTable.query.get_or_404(job_id)
    employer = EmployerProfile.query.get(job.link_to_employer_profile)

    # Log view
    log = JobViewsLog(job_id=job_id, viewed_at=date.today())
    db.session.add(log)
    job.views = (job.views or 0) + 1
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()

    return render_template('job_details.html', job=job, employer=employer)


@main_bp.route('/apply/<int:job_id>', methods=['GET', 'POST'])
def apply(job_id):
    job = AdvertisingTable.query.get_or_404(job_id)

    if request.method == 'POST':
        guest_name = request.form.get('guest_full_name', '').strip()
        guest_contact = request.form.get('guest_contact_no', '').strip()
        guest_gender = request.form.get('guest_gender', '')
        cv_file = request.files.get('guest_cv')
        cl_file = request.files.get('guest_cover_letter')

        if not guest_name or not guest_contact or not cv_file:
            flash('Name, contact number and CV are required.', 'danger')
            return render_template('apply.html', job=job)

        cv_path = upload_svc.save_file(cv_file, 'cvs',
                                       current_app.config['ALLOWED_DOC_EXTENSIONS'])
        cl_path = upload_svc.save_file(cl_file, 'cl',
                                       current_app.config['ALLOWED_DOC_EXTENSIONS']) if cl_file else None

        app_entry = GuestJobApplication(
            job_ad_link=job_id,
            guest_full_name=guest_name,
            guest_contact_no=guest_contact,
            guest_gender=guest_gender,
            guest_cv=b'',
            cv_path=cv_path,
            cl_path=cl_path,
        )
        db.session.add(app_entry)
        db.session.commit()
        flash('Application submitted successfully!', 'success')
        return redirect(url_for('main.job_details', job_id=job_id))

    return render_template('apply.html', job=job)


@main_bp.route('/get-cities')
def get_cities():
    district = request.args.get('district', '')
    cities = City.query.join(District, City.City_link == District.id)\
                       .filter(District.District_name == district)\
                       .order_by(City.City).all()
    return jsonify([{'id': c.id, 'name': c.City} for c in cities])


@main_bp.route('/fetch-jobs')
def fetch_jobs():
    keyword = request.args.get('keyword', '')
    district = request.args.get('district', '')
    city = request.args.get('city', '')
    category = request.args.get('category', '')
    job_type = request.args.get('job_type', '')

    query = (AdvertisingTable.query
             .filter(AdvertisingTable.Approved == 1,
                     AdvertisingTable.Closing_date >= date.today()))

    if keyword:
        query = query.filter(AdvertisingTable.Job_role.ilike(f'%{keyword}%'))
    if district:
        query = query.filter(AdvertisingTable.District == district)
    if city:
        query = query.filter(AdvertisingTable.City == city)
    if category:
        query = query.filter(AdvertisingTable.Job_category == category)
    if job_type:
        query = query.filter(AdvertisingTable.job_type == job_type)

    jobs = query.order_by(AdvertisingTable.id.desc()).limit(50).all()
    result = [{
        'id': j.id,
        'title': j.Job_role,
        'category': j.Job_category,
        'type': j.job_type,
        'district': j.District,
        'city': j.City,
        'closing_date': j.Closing_date.isoformat() if j.Closing_date else '',
    } for j in jobs]
    return jsonify(result)


@main_bp.route('/select-dashboard')
def select_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('select_dashboard.html')


@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()
        if name and email and message:
            from services.mail import send_email
            admin_email = SiteSetting.query.filter_by(setting_key='admin_email').first()
            if admin_email:
                send_email(admin_email.setting_value,
                           f'Contact Form: {name}',
                           f'<p>From: {name} ({email})</p><p>{message}</p>')
            flash('Your message has been sent!', 'success')
        else:
            flash('Please fill in all fields.', 'danger')
        return redirect(url_for('main.contact'))
    return render_template('contact.html')


@main_bp.route('/policies')
def policies():
    return render_template('policies.html')


@main_bp.route('/paper-ads')
def paper_ads():
    return render_template('paper_ads.html')
