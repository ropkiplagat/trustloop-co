"""
TrustLoop admin auth — HMAC-signed tokens, no external deps.
Starting password: TrustLoop@Admin2026 — rotate immediately after first login.
"""
import os
import hashlib
import hmac
import time
import json
import base64

JWT_SECRET      = os.getenv('JWT_SECRET', 'trustloop-change-this-secret-in-env')
ADMIN_PASSWORD  = os.getenv('ADMIN_PASSWORD', 'TrustLoop@Admin2026')
TOKEN_TTL_SECS  = 8 * 3600  # 8 hours


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def check_password(password: str) -> bool:
    return hmac.compare_digest(
        _hash_password(password),
        _hash_password(ADMIN_PASSWORD)
    )


def make_token() -> str:
    header  = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').decode().rstrip('=')
    payload = json.dumps({'role': 'admin', 'exp': int(time.time()) + TOKEN_TTL_SECS})
    body    = base64.urlsafe_b64encode(payload.encode()).decode().rstrip('=')
    msg     = f'{header}.{body}'
    sig     = hmac.new(JWT_SECRET.encode(), msg.encode(), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).decode().rstrip('=')
    return f'{msg}.{sig_b64}'


def verify_token(token: str) -> bool:
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return False
        header, body, sig = parts
        msg      = f'{header}.{body}'
        expected = hmac.new(JWT_SECRET.encode(), msg.encode(), hashlib.sha256).digest()
        exp_b64  = base64.urlsafe_b64encode(expected).decode().rstrip('=')
        if not hmac.compare_digest(sig, exp_b64):
            return False
        payload = json.loads(base64.urlsafe_b64decode(body + '==').decode())
        return payload.get('exp', 0) > time.time()
    except Exception:
        return False


def token_from_request(request) -> str | None:
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        return auth[7:]
    return request.args.get('token') or None
