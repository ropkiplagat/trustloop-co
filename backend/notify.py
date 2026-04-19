"""
TrustLoop Notifications — SMS only via ConnectBind (RouteMobile)
Email notifications handled by SiteGround (not this service).
"""
import os
import urllib.parse
import urllib.request
from datetime import datetime

CB_USERNAME = os.getenv('CB_USERNAME', '')
CB_PASSWORD = os.getenv('CB_PASSWORD', '')
CB_SENDER   = os.getenv('CB_SENDER',   'TRSTLP')
CB_BASE     = 'https://rslr.connectbind.com:8443/bulksms/bulksms'


def send_sms(phone: str, message: str) -> bool:
    if not CB_USERNAME or not CB_PASSWORD:
        _mock_sms(phone, message)
        return True
    return _connectbind_sms(phone, message)


def _mock_sms(phone: str, message: str):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[SMS MOCK] {ts} → {phone}: {message}")
    print(f"[SMS MOCK] Set CB_USERNAME + CB_PASSWORD in .env to enable live SMS")


def _connectbind_sms(phone: str, message: str) -> bool:
    try:
        phone = phone.replace(' ', '').replace('-', '')
        if phone.startswith('+'):
            phone = phone[1:]
        elif phone.startswith('07') or phone.startswith('01'):
            phone = '254' + phone[1:]
        elif not phone.startswith('254'):
            phone = '254' + phone

        params = urllib.parse.urlencode({
            'username':    CB_USERNAME,
            'password':    CB_PASSWORD,
            'type':        '0',
            'dlr':         '1',
            'destination': phone,
            'source':      CB_SENDER,
            'message':     message,
        })
        url  = f"{CB_BASE}?{params}"
        req  = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=15)
        body = resp.read().decode('utf-8', errors='replace').strip()
        print(f"[SMS] ConnectBind → {phone}: {body}")
        success = body.startswith('1701') or 'success' in body.lower()
        if not success:
            print(f"[SMS] Unexpected response: {body}")
        return success
    except Exception as e:
        print(f"[SMS] Error for {phone}: {e}")
        _mock_sms(phone, message)
        return False


def notify_submission(application: dict):
    name  = application.get('full_name', 'Applicant')
    ref   = application.get('ref', '—')
    phone = application.get('phone', '')
    sms_msg = (
        f"TrustLoop: Hi {name.split()[0]}, your application {ref} "
        f"has been received. Credit score ready within 2hrs. Ref: {ref}"
    )
    send_sms(phone, sms_msg)


def notify_score_ready(application: dict, score_result: dict):
    name  = application.get('full_name', 'Applicant')
    ref   = application.get('ref', '—')
    phone = application.get('phone', '')
    score = score_result.get('score', 0)
    rating = score_result.get('rating', '—')
    status = 'Approved' if score >= 700 else 'Conditional' if score >= 580 else 'Declined'
    sms_msg = (
        f"TrustLoop: Hi {name.split()[0]}, score ready. "
        f"{score}/850 ({rating}) — {status}. "
        f"Ref: {ref}. trustloopafrica.com"
    )
    send_sms(phone, sms_msg)


if __name__ == '__main__':
    test_app   = {'full_name': 'Jane Wanjiku', 'ref': 'TL-123456', 'phone': '0712345678'}
    test_score = {'score': 712, 'rating': 'Good', 'recommendation': 'Approved at standard rate.'}
    notify_submission(test_app)
    notify_score_ready(test_app, test_score)
