from flask_mail import Mail, Message

mail = Mail()


def send_email(to, subject, html_body):
    msg = Message(subject=subject, recipients=[to], html=html_body)
    try:
        mail.send(msg)
        return True
    except Exception as e:
        import logging
        logging.error(f"Mail send failed to {to}: {e}")
        return False
