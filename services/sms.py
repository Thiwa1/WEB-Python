import requests
from flask import current_app


def send_sms(phone_number, message):
    user_id = current_app.config.get('SMS_USER_ID', '')
    api_key = current_app.config.get('SMS_API_KEY', '')
    sender_id = current_app.config.get('SMS_SENDER_ID', 'NotifyDEMO')

    if not user_id or not api_key:
        import logging
        logging.warning("SMS not configured — skipping send")
        return False

    try:
        resp = requests.get(
            'https://app.notify.lk/api/v1/send',
            params={
                'user_id': user_id,
                'api_key': api_key,
                'sender_id': sender_id,
                'to': phone_number,
                'message': message,
            },
            timeout=10,
        )
        data = resp.json()
        return data.get('status') == 'success'
    except Exception as e:
        import logging
        logging.error(f"SMS send failed: {e}")
        return False
