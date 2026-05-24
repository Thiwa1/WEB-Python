from datetime import datetime
from database import db


class UserType(db.Model):
    __tablename__ = 'user_type_table'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_type_select = db.Column(db.String(45), unique=True, nullable=False)
    type_hide = db.Column(db.SmallInteger, default=0)


class User(db.Model):
    __tablename__ = 'user_table'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_email = db.Column(db.String(200), unique=True, nullable=False)
    user_password = db.Column(db.LargeBinary(255), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    Birthday = db.Column(db.Date, nullable=False)
    male_female = db.Column(db.String(45), nullable=False)
    user_type = db.Column(db.String(45), db.ForeignKey('user_type_table.user_type_select'), nullable=False)
    mobile_number = db.Column(db.String(20), unique=True, nullable=False)
    WhatsApp_number = db.Column(db.String(20), unique=True, nullable=False)
    max_login_attempt = db.Column(db.Integer, default=0)
    user_active = db.Column(db.SmallInteger, default=1)
    country = db.Column(db.String(45), default='Sri Lanka')
    send_opt = db.Column(db.Integer)
    send_time = db.Column(db.DateTime)
    max_validate_time = db.Column(db.Integer)
    user_block = db.Column(db.SmallInteger, default=0)
    is_paper_admin = db.Column(db.SmallInteger, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class EmployerProfile(db.Model):
    __tablename__ = 'employer_profile'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    link_to_user = db.Column(db.Integer, db.ForeignKey('user_table.id'), unique=True, nullable=False)
    employer_name = db.Column(db.String(200), unique=True)
    employer_address_1 = db.Column(db.String(45))
    employer_address_2 = db.Column(db.String(45))
    employer_address_3 = db.Column(db.String(45))
    employer_logo = db.Column(db.LargeBinary(16777215))
    employer_BR = db.Column(db.LargeBinary(16777215))
    employer = db.Column(db.String(20), unique=True)
    employer_mobile_no = db.Column(db.String(20), unique=True)
    employer_whatsapp_no = db.Column(db.String(20), unique=True)
    employer_about_company = db.Column(db.Text)
    employer_Verified = db.Column(db.SmallInteger, default=0)
    employer_Verified_by = db.Column(db.String(100))
    logo_path = db.Column(db.String(255))
    br_path = db.Column(db.String(255))


class EmployeeProfileSeeker(db.Model):
    __tablename__ = 'employee_profile_seeker'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    link_to_user = db.Column(db.Integer, db.ForeignKey('user_table.id'), unique=True, nullable=False)
    employee_full_name = db.Column(db.String(200))
    employee_name_with_initial = db.Column(db.String(100))
    employee_cv = db.Column(db.LargeBinary(16777215))
    employee_cover_letter = db.Column(db.LargeBinary(16777215))
    employee_img = db.Column(db.LargeBinary(16777215))
    img_path = db.Column(db.String(255))
    cv_path = db.Column(db.String(255))
    cl_path = db.Column(db.String(255))


class District(db.Model):
    __tablename__ = 'district_table'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    District_name = db.Column(db.String(45), unique=True)
    cities = db.relationship('City', backref='district', lazy=True)


class City(db.Model):
    __tablename__ = 'city_table'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    City = db.Column(db.String(45), unique=True)
    City_link = db.Column(db.Integer, db.ForeignKey('district_table.id'))


class JobCategory(db.Model):
    __tablename__ = 'job_category_table'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Description = db.Column(db.String(45), unique=True)


class IndustrySetting(db.Model):
    __tablename__ = 'Industry_Setting'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Industry_name = db.Column(db.String(45))


class AdvertisingTable(db.Model):
    __tablename__ = 'advertising_table'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    link_to_employer_profile = db.Column(db.Integer, db.ForeignKey('employer_profile.id'), nullable=False)
    Opening_date = db.Column(db.Date)
    Closing_date = db.Column(db.Date)
    Industry = db.Column(db.String(255))
    Job_category = db.Column(db.String(255), db.ForeignKey('job_category_table.Description'))
    Job_role = db.Column(db.String(255))
    job_type = db.Column(db.String(50), default='Full Time')
    Img = db.Column(db.LargeBinary(16777215))
    City = db.Column(db.String(45), db.ForeignKey('city_table.City'))
    job_description = db.Column(db.Text)
    District = db.Column(db.String(45), db.ForeignKey('district_table.District_name'))
    Apply_by_email = db.Column(db.SmallInteger, default=0)
    Apply_by_system = db.Column(db.SmallInteger, default=1)
    apply_WhatsApp = db.Column(db.SmallInteger, default=0)
    Apply_by_email_address = db.Column(db.String(200))
    apply_WhatsApp_No = db.Column(db.String(20))
    Approved = db.Column(db.SmallInteger, default=0)
    Rejection_comment = db.Column(db.String(200))
    rejection_reason = db.Column(db.String(255))
    views = db.Column(db.Integer, default=0)
    img_path = db.Column(db.String(255))


class JobApplication(db.Model):
    __tablename__ = 'job_applications'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    job_ad_link = db.Column(db.Integer, db.ForeignKey('advertising_table.id'), nullable=False)
    seeker_link = db.Column(db.Integer, db.ForeignKey('employee_profile_seeker.id'), nullable=False)
    applied_date = db.Column(db.DateTime, default=datetime.utcnow)
    application_status = db.Column(db.String(45), default='Pending')
    rejection_reason = db.Column(db.String(255))


class GuestJobApplication(db.Model):
    __tablename__ = 'guest_job_applications'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    job_ad_link = db.Column(db.Integer, db.ForeignKey('advertising_table.id'), nullable=False)
    guest_full_name = db.Column(db.String(200), nullable=False)
    guest_contact_no = db.Column(db.String(20), nullable=False)
    guest_gender = db.Column(db.String(10), nullable=False)
    guest_cv = db.Column(db.LargeBinary(16777215), nullable=False)
    guest_cover_letter = db.Column(db.LargeBinary(16777215))
    applied_date = db.Column(db.DateTime, default=datetime.utcnow)
    application_status = db.Column(db.String(45), default='Pending')
    rejection_reason = db.Column(db.String(255))
    cv_path = db.Column(db.String(255))
    cl_path = db.Column(db.String(255))


class PaymentTable(db.Model):
    __tablename__ = 'payment_table'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employer_link = db.Column(db.Integer, db.ForeignKey('employer_profile.id'))
    VAT_enable = db.Column(db.SmallInteger, default=0)
    Totaled_received = db.Column(db.Float, default=0)
    Payment_slip = db.Column(db.LargeBinary(16777215))
    Approval = db.Column(db.SmallInteger, default=0)
    payment_date = db.Column(db.Date)
    Approval_date = db.Column(db.Date)
    Reject_comment = db.Column(db.String(100))
    slip_path = db.Column(db.String(255))


class PaidAdvertising(db.Model):
    __tablename__ = 'paid_advertising'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    slip_link = db.Column(db.Integer, db.ForeignKey('payment_table.id'))
    add_link = db.Column(db.Integer, db.ForeignKey('advertising_table.id'))
    paid = db.Column(db.SmallInteger, default=0)
    __table_args__ = (db.UniqueConstraint('add_link', 'slip_link'),)


class SiteSetting(db.Model):
    __tablename__ = 'site_settings'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    setting_key = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SystemBankAccount(db.Model):
    __tablename__ = 'system_bank_accounts'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bank_name = db.Column(db.String(255), nullable=False)
    account_number = db.Column(db.String(100), nullable=False)
    branch_name = db.Column(db.String(100))
    branch_code = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class EmployeeAlertSetting(db.Model):
    __tablename__ = 'employee_alerted_setting'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    district = db.Column(db.String(45))
    city = db.Column(db.String(45))
    job_category = db.Column(db.String(45))
    link_to_employee_profile = db.Column(db.Integer)
    active = db.Column(db.SmallInteger, default=1)
    Total_count = db.Column(db.Integer, default=0)
    last_alert_sent = db.Column(db.DateTime)


class EmployeeDocument(db.Model):
    __tablename__ = 'employee_document'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    link_to_employee_profile = db.Column(db.Integer)
    document_type = db.Column(db.String(45))
    document = db.Column(db.LargeBinary(16777215))
    doc_path = db.Column(db.String(255))


class TalentOffer(db.Model):
    __tablename__ = 'talent_offers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    seeker_link = db.Column(db.Integer, db.ForeignKey('employee_profile_seeker.id'), nullable=False)
    headline = db.Column(db.String(255), nullable=False)
    skills_tags = db.Column(db.Text)
    experience_years = db.Column(db.Integer, default=0)
    expected_salary = db.Column(db.Float, default=0)
    description = db.Column(db.Text)
    expiry_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.SmallInteger, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PriceSetting(db.Model):
    __tablename__ = 'Price_setting'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Unit_of_add = db.Column(db.Integer)
    selling_price = db.Column(db.Float)


class CompanyDetails(db.Model):
    __tablename__ = 'Compan_details'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_name = db.Column(db.String(255))
    Compan_detailscol = db.Column(db.String(255))
    addres1 = db.Column(db.String(255))
    addres2 = db.Column(db.String(255))
    addres3 = db.Column(db.String(255))
    TP_No = db.Column(db.String(255))
    logo = db.Column(db.LargeBinary(16777215))
    logo_path = db.Column(db.String(255))


class JobViewsLog(db.Model):
    __tablename__ = 'job_views_log'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    job_id = db.Column(db.Integer, db.ForeignKey('advertising_table.id'))
    viewed_at = db.Column(db.Date, default=datetime.utcnow)


class SmsLog(db.Model):
    __tablename__ = 'sms_logs'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    job_id = db.Column(db.Integer, db.ForeignKey('advertising_table.id'), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='Sent')
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)


class AdminLoginLog(db.Model):
    __tablename__ = 'admin_login_logs'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    login_time = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))


class PaperAd(db.Model):
    __tablename__ = 'paper_ads'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employer_link = db.Column(db.Integer, db.ForeignKey('employer_profile.id'))
    ad_text = db.Column(db.Text)
    contact_info = db.Column(db.String(255))
    status = db.Column(db.String(45), default='Pending')
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime)
    slip_path = db.Column(db.String(255))
