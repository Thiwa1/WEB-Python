import requests
from flask import current_app


def verify(token, action=None, min_score=0.5):
    secret = current_app.config.get('RECAPTCHA_SECRET_KEY', '')
    if not secret or not token:
        return True  # skip in dev if not configured

    resp = requests.post(
        'https://www.google.com/recaptcha/api/siteverify',
        data={'secret': secret, 'response': token},
        timeout=5,
    )
    result = resp.json()
    if not result.get('success'):
        return False
    if action and result.get('action') != action:
        return False
    return result.get('score', 0) >= min_score
