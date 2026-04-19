"""
TrustLoop Notifications
- SMS: RouteMobile mock (console print) until Abraham provides API key
- Email: Gmail SMTP via rop@targetdigital.com.au
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ── Gmail SMTP config ──
GMAIL_USER     = os.getenv('GMAIL_USER',     'rop@targetdigital.com.au')
GMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD', '')   # set in .env on VPS

# ── RouteMobile SMS config (plug in when Abraham provides key) ──
ROUTEMOBILE_API_KEY  = os.getenv('ROUTEMOBILE_API_KEY', '')
ROUTEMOBILE_SENDER   = os.getenv('ROUTEMOBILE_SENDER',  'TrustLoop')
ROUTEMOBILE_BASE     = 'https://api.routemobile.com/sms/2/text/single'


# ──────────────────────────────────────────────
# SMS
# ──────────────────────────────────────────────

def send_sms(phone: str, message: str) -> bool:
    """
    Send SMS via RouteMobile.
    Falls back to console mock if API key not set.
    """
    if not ROUTEMOBILE_API_KEY:
        _mock_sms(phone, message)
        return True
    return _routemobile_sms(phone, message)


def _mock_sms(phone: str, message: str):
    """Console mock — replace with real API when Abraham sends key."""
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[SMS MOCK] Sent to {phone} at {ts}")
    print(f"[SMS MOCK] Message: {message}")
    print(f"[SMS MOCK] RouteMobile key not set — plug in ROUTEMOBILE_API_KEY env var")


def _routemobile_sms(phone: str, message: str) -> bool:
    """Live RouteMobile API call."""
    try:
        import requests
        # Normalise to international format for Kenya
        if phone.startswith('07') or phone.startswith('01'):
            phone = '+254' + phone[1:]
        elif phone.startswith('254'):
            phone = '+' + phone

        payload = {
            'from':    ROUTEMOBILE_SENDER,
            'to':      phone,
            'text':    message,
        }
        resp = requests.post(
            ROUTEMOBILE_BASE,
            json=payload,
            headers={
                'Authorization': f'App {ROUTEMOBILE_API_KEY}',
                'Content-Type':  'application/json',
            },
            timeout=10
        )
        resp.raise_for_status()
        print(f"[SMS] Sent to {phone} — status {resp.status_code}")
        return True
    except Exception as e:
        print(f"[SMS] Failed to send to {phone}: {e}")
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
