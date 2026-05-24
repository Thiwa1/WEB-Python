import os
from flask import Flask
from flask_mail import Mail
from config import config
from database import db
from services.mail import mail


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Init extensions
    db.init_app(app)
    mail.init_app(app)

    # Register blueprints
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.employer import employer_bp
    from routes.employee import employee_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(employer_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(admin_bp)

    # Create DB tables
    with app.app_context():
        db.create_all()
        _seed_defaults()

    return app


def _seed_defaults():
    from models import UserType, SiteSetting
    if not UserType.query.first():
        for t in ('employer', 'employee', 'admin', 'paperadmin'):
            db.session.add(UserType(user_type_select=t, type_hide=0))
        db.session.commit()

    for key, val in [('promo_active', '0'), ('admin_email', ''), ('site_name', 'JobPortal Pro')]:
        if not SiteSetting.query.filter_by(setting_key=key).first():
            db.session.add(SiteSetting(setting_key=key, setting_value=val))
    db.session.commit()


app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
