"""
TrustLoop Notifications
- SMS: ConnectBind (RouteMobile) via rslr.connectbind.com:8443
- Email: Gmail SMTP via rop@targetdigital.com.au
"""
import os
import urllib.parse
import urllib.request
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ── Gmail SMTP config ──
GMAIL_USER     = os.getenv('GMAIL_USER',     'rop@targetdigital.com.au')
GMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD', '')

# ── ConnectBind SMS config ──
CB_USERNAME = os.getenv('CB_USERNAME', '')          # set in .env
CB_PASSWORD = os.getenv('CB_PASSWORD', '')          # set in .env
CB_SENDER   = os.getenv('CB_SENDER',   'TRSTLP')   # max 6 chars alphanumeric
CB_BASE     = 'https://rslr.connectbind.com:8443/bulksms/bulksms'


# ──────────────────────────────────────────────
# SMS
# ──────────────────────────────────────────────

def send_sms(phone: str, message: str) -> bool:
    """Send SMS via ConnectBind. Falls back to console mock if creds not set."""
    if not CB_USERNAME or not CB_PASSWORD:
        _mock_sms(phone, message)
        return True
    return _connectbind_sms(phone, message)


def _mock_sms(phone: str, message: str):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[SMS MOCK] Sent to {phone} at {ts}")
    print(f"[SMS MOCK] Message: {message}")
    print(f"[SMS MOCK] Set CB_USERNAME + CB_PASSWORD in .env to enable live SMS")


def _connectbind_sms(phone: str, message: str) -> bool:
    """Live ConnectBind SMS via GET request."""
    try:
        # Normalise to Kenya international format (digits only, no +)
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
        print(f"[SMS] ConnectBind response for {phone}: {body}")
        # ConnectBind returns '1701' or similar code on success
        success = body.startswith('1701') or 'success' in body.lower()
        if not success:
            print(f"[SMS] Unexpected response: {body}")
        return success
    except Exception as e:
        print(f"[SMS] ConnectBind error for {phone}: {e}")
        _mock_sms(phone, message)
        return False


# ──────────────────────────────────────────────
# Email
# ──────────────────────────────────────────────

def send_email(to: str, subject: str, body_html: str, body_text: str = '') -> bool:
    """Send email via Gmail SMTP."""
    if not GMAIL_PASSWORD:
        print(f"[EMAIL MOCK] Would send to {to}")
        print(f"[EMAIL MOCK] Subject: {subject}")
        print(f"[EMAIL MOCK] Set GMAIL_PASSWORD env var to enable real sending")
        return True
    try:
        msg = MIMEMultipart('alternative')
        msg['From']    = GMAIL_USER
        msg['To']      = to
        msg['Subject'] = subject
        if body_text:
            msg.attach(MIMEText(body_text, 'plain'))
        msg.attach(MIMEText(body_html, 'html'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.sendmail(GMAIL_USER, to, msg.as_string())

        print(f"[EMAIL] Sent to {to} — {subject}")
        return True
    except Exception as e:
        print(f"[EMAIL] Failed to {to}: {e}")
        return False


# ──────────────────────────────────────────────
# Notification Templates
# ──────────────────────────────────────────────

def notify_submission(application: dict):
    """Notify applicant that we received their application."""
    name  = application.get('full_name', 'Applicant')
    ref   = application.get('ref', '—')
    phone = application.get('phone', '')

    sms_msg = (
        f"TrustLoop: Hi {name.split()[0]}, your application {ref} "
        f"has been received. We'll send your credit score within 2hrs. "
        f"Ref: {ref}"
    )
    send_sms(phone, sms_msg)

    email_html = f"""
    <div style="font-family:Inter,sans-serif;max-width:560px;margin:0 auto;background:#0a0f0d;color:#e4f0e8;padding:32px;border-radius:12px;">
      <h2 style="color:#00c853;">Application Received ✓</h2>
      <p>Hi {name},</p>
      <p>We've received your loan application on <strong>TrustLoop</strong>.</p>
      <table style="width:100%;border-collapse:collapse;margin:20px 0;">
        <tr><td style="color:#6b9e7a;padding:8px 0;">Reference</td><td style="font-weight:700;">{ref}</td></tr>
        <tr><td style="color:#6b9e7a;padding:8px 0;">Status</td><td style="color:#00c853;font-weight:700;">Pending Review</td></tr>
        <tr><td style="color:#6b9e7a;padding:8px 0;">Expected</td><td>Within 2 business hours</td></tr>
      </table>
      <p style="color:#6b9e7a;font-size:13px;">TrustLoop · Powered by SpinMobile Credit Intelligence</p>
    </div>
    """
    # Send to applicant (if email was collected — extend form later)
    # For now send confirmation to admin
    send_email(GMAIL_USER, f"[TrustLoop] New Application — {ref}", email_html)


def notify_score_ready(application: dict, score_result: dict):
    """Notify applicant and admin when score is computed."""
    name    = application.get('full_name', 'Applicant')
    ref     = application.get('ref', '—')
    phone   = application.get('phone', '')
    score   = score_result.get('score', 0)
    rating  = score_result.get('rating', '—')
    rec     = score_result.get('recommendation', '—')

    eligible = score >= 580
    status   = 'Approved' if score >= 700 else 'Conditional' if eligible else 'Declined'

    sms_msg = (
        f"TrustLoop: Hi {name.split()[0]}, your credit score is ready. "
        f"Score: {score}/850 ({rating}). Status: {status}. "
        f"Ref: {ref}. Visit trustloop.co to view full report."
    )
    send_sms(phone, sms_msg)

    email_html = f"""
    <div style="font-family:Inter,sans-serif;max-width:560px;margin:0 auto;background:#0a0f0d;color:#e4f0e8;padding:32px;border-radius:12px;">
      <h2 style="color:#00c853;">Your Credit Score is Ready</h2>
      <p>Hi {name},</p>
      <div style="background:#0d1510;border:1px solid #1e3328;border-radius:10px;padding:24px;text-align:center;margin:20px 0;">
        <div style="font-size:48px;font-weight:900;color:#00c853;">{score}</div>
        <div style="color:#6b9e7a;margin-top:4px;">out of 850 · {rating}</div>
        <div style="margin-top:12px;font-weight:700;color:{'#00c853' if eligible else '#ff3b3b'};">{status}</div>
      </div>
      <p style="color:#6b9e7a;">{rec}</p>
      <p style="color:#6b9e7a;font-size:13px;">Reference: {ref} · TrustLoop Credit Intelligence</p>
    </div>
    """
    # Notify admin (Abraham)
    send_email(GMAIL_USER, f"[TrustLoop] Score Ready — {ref} — {score}/850 ({status})", email_html)


if __name__ == '__main__':
    test_app = {'full_name': 'Jane Wanjiku', 'ref': 'TL-123456', 'phone': '0712345678'}
    test_score = {'score': 712, 'rating': 'Good', 'recommendation': 'Approved at standard rate.'}
    notify_submission(test_app)
    notify_score_ready(test_app, test_score)
