from google.oauth2 import id_token
from google.auth.transport import requests as grequests
from flask import current_app, url_for
import requests


GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v2/userinfo'


def get_auth_url(state=None):
    client_id = current_app.config['GOOGLE_CLIENT_ID']
    redirect_uri = url_for('auth.google_callback', _external=True)
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'access_type': 'offline',
    }
    if state:
        params['state'] = state
    query = '&'.join(f"{k}={v}" for k, v in params.items())
    return f"{GOOGLE_AUTH_URL}?{query}"


def exchange_code(code):
    client_id = current_app.config['GOOGLE_CLIENT_ID']
    client_secret = current_app.config['GOOGLE_CLIENT_SECRET']
    redirect_uri = url_for('auth.google_callback', _external=True)

    resp = requests.post(GOOGLE_TOKEN_URL, data={
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
    })
    return resp.json()


def get_user_info(access_token):
    resp = requests.get(
        GOOGLE_USERINFO_URL,
        headers={'Authorization': f'Bearer {access_token}'},
    )
    return resp.json()
