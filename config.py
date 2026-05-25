import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-change-in-prod')
    # Flask-Session 0.5.0 (Python 3.8 compatible)
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask_session')
    SESSION_USE_SIGNER = True
    SESSION_PERMANENT = False

    # Database
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_NAME = os.environ.get('DB_NAME', 'suwixvkn_vacancies')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
        "?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Mail
    MAIL_SERVER = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('SMTP_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('SMTP_USER', '')
    MAIL_PASSWORD = os.environ.get('SMTP_PASS', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_FROM', os.environ.get('SMTP_USER', ''))

    # reCAPTCHA
    RECAPTCHA_SITE_KEY = os.environ.get('RECAPTCHA_SITE_KEY', '')
    RECAPTCHA_SECRET_KEY = os.environ.get('RECAPTCHA_SECRET_KEY', '')

    # Google OAuth
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')

    # SMS
    SMS_USER_ID = os.environ.get('SMS_USER_ID', '')
    SMS_API_KEY = os.environ.get('SMS_API_KEY', '')
    SMS_SENDER_ID = os.environ.get('SMS_SENDER_ID', 'NotifyDEMO')

    # Uploads
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ALLOWED_DOC_EXTENSIONS = {'pdf', 'doc', 'docx'}

    APP_URL = os.environ.get('APP_URL', 'http://localhost:5000')


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
