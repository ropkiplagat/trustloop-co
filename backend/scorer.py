"""
TrustLoop Credit Scorer — provider abstraction
SCORER_PROVIDER env var selects: mock (default) | spinmobile | metropol
Flip to live: set SCORER_PROVIDER=spinmobile + API key, then restart.
"""
import os
import json
import math
from datetime import datetime

SCORER_PROVIDER    = os.getenv('SCORER_PROVIDER', 'mock').lower()
SPINMOBILE_API_KEY = os.getenv('SPINMOBILE_API_KEY', '')
SPINMOBILE_BASE    = os.getenv('SPINMOBILE_BASE_URL', 'https://api.spinmobile.co/v1')
METROPOL_API_KEY   = os.getenv('METROPOL_API_KEY', '')
METROPOL_BASE      = os.getenv('METROPOL_BASE_URL', 'https://api.metropol.co.ke/v2')

SCORE_MIN = 300
SCORE_MAX = 850

PROVIDERS = {
    'mock':       {'ready': True,                    'label': 'Mock (local)'},
    'spinmobile': {'ready': bool(SPINMOBILE_API_KEY), 'label': 'SpinMobile'},
    'metropol':   {'ready': bool(METROPOL_API_KEY),   'label': 'Metropol CRB'},
}


def compute_score(application: dict, pdf_data: dict) -> dict:
    provider = SCORER_PROVIDER
    if provider == 'spinmobile' and SPINMOBILE_API_KEY:
        return _spinmobile_score(application, pdf_data)
    if provider == 'metropol' and METROPOL_API_KEY:
        return _metropol_score(application, pdf_data)
    if provider != 'mock':
        print(f"[SCORER] Provider '{provider}' selected but key missing — falling back to mock")
    return _mock_score(application, pdf_data)


def provider_status() -> dict:
    return {k: v for k, v in PROVIDERS.items()}


# ── SpinMobile ────────────────────────────────────────────────────────────────

def _spinmobile_score(application: dict, pdf_data: dict) -> dict:
    try:
        import requests
        payload = {
            'phone':          application.get('phone', ''),
            'national_id':    application.get('national_id', ''),
            'monthly_income': application.get('monthly_income', 0),
            'loan_amount':    application.get('loan_amount', 0),
            'tx_count':       pdf_data.get('tx_count', 0),
            'total_in':       pdf_data.get('total_in', 0),
            'total_out':      pdf_data.get('total_out', 0),
            'net_flow':       pdf_data.get('net_flow', 0),
            'utilisation':    pdf_data.get('utilisation', 0),
        }
        resp = requests.post(
            f'{SPINMOBILE_BASE}/score',
            json=payload,
            headers={'Authorization': f'Bearer {SPINMOBILE_API_KEY}'},
            timeout=15
        )
        resp.raise_for_status()
        return _normalise_spinmobile(resp.json())
    except Exception as e:
        print(f"[SCORER] SpinMobile error: {e} — falling back to mock")
        return _mock_score(application, pdf_data)


def _normalise_spinmobile(data: dict) -> dict:
    score = int(data.get('credit_score', data.get('score', 500)))
    return {
        'score':          score,
        'rating':         _rating(score),
        'breakdown':      data.get('breakdown', {}),
        'recommendation': _recommendation(score),
        'source':         'spinmobile',
        'scored_at':      datetime.now().isoformat(),
    }


# ── Metropol CRB ──────────────────────────────────────────────────────────────

def _metropol_score(application: dict, pdf_data: dict) -> dict:
    try:
        import requests
        payload = {
            'id_number':   application.get('national_id', ''),
            'phone':       application.get('phone', ''),
            'loan_amount': application.get('loan_amount', 0),
        }
        resp = requests.post(
            f'{METROPOL_BASE}/credit-score',
            json=payload,
            headers={
                'X-API-Key': METROPOL_API_KEY,
                'Content-Type': 'application/json',
            },
            timeout=15
        )
        resp.raise_for_status()
        return _normalise_metropol(resp.json())
    except Exception as e:
        print(f"[SCORER] Metropol error: {e} — falling back to mock")
        return _mock_score(application, pdf_data)


def _normalise_metropol(data: dict) -> dict:
    score = int(data.get('score', data.get('credit_score', 500)))
    return {
        'score':          score,
        'rating':         _rating(score),
        'breakdown':      data.get('factors', {}),
        'recommendation': _recommendation(score),
        'source':         'metropol',
        'scored_at':      datetime.now().isoformat(),
    }


# ── Mock ──────────────────────────────────────────────────────────────────────

def _mock_score(application: dict, pdf_data: dict) -> dict:
    score = SCORE_MIN

    income  = float(application.get('monthly_income', 0))
    amount  = float(application.get('loan_amount', 0))
    emp     = application.get('employment', '')

    total_in    = float(pdf_data.get('total_in',    0))
    total_out   = float(pdf_data.get('total_out',   0))
    tx_count    = int(pdf_data.get('tx_count',      0))
    utilisation = float(pdf_data.get('utilisation', 0.8))
    net_flow    = float(pdf_data.get('net_flow',    0))

    breakdown = {}

    pay_pts = min(tx_count / 180 * (0.35 * SCORE_MAX), 0.35 * SCORE_MAX)
    breakdown['payment_history'] = round(pay_pts)
    score += pay_pts

    if income > 0 and total_in > 0:
        ratio = min(total_in / (income * 3), 1.2)
        inc_pts = ratio * 0.30 * SCORE_MAX
    else:
        inc_pts = 0.15 * SCORE_MAX
    breakdown['income_flow'] = round(inc_pts)
    score += inc_pts

    util_pts = (1 - min(utilisation, 1.0)) * 0.20 * SCORE_MAX
    breakdown['utilisation'] = round(util_pts)
    score += util_pts

    if income > 0:
        lti = amount / (income * 12)
        lti_pts = max(0, 1 - lti) * 0.15 * SCORE_MAX
    else:
        lti_pts = 0.075 * SCORE_MAX
    breakdown['loan_to_income'] = round(lti_pts)
    score += lti_pts

    emp_bonus = {'Employed (Formal)': 30, 'Self-Employed': 15, 'Farmer': 10, 'Casual Worker': 5}
    score += emp_bonus.get(emp, 0)

    if net_flow > 0:
        score += min(net_flow / 50000 * 20, 20)

    score = max(SCORE_MIN, min(SCORE_MAX, round(score)))

    return {
        'score':          score,
        'rating':         _rating(score),
        'breakdown':      breakdown,
        'recommendation': _recommendation(score),
        'source':         'mock',
        'scored_at':      datetime.now().isoformat(),
    }


def _rating(score: int) -> str:
    if score >= 750: return 'Excellent'
    if score >= 700: return 'Good'
    if score >= 640: return 'Fair'
    if score >= 580: return 'Below Average'
    return 'Poor'


def _recommendation(score: int) -> str:
    if score >= 700:
        return 'Approved — applicant qualifies for requested amount at standard rate.'
    if score >= 580:
        return 'Conditional — approve at reduced amount or request guarantor.'
    return 'Declined — insufficient credit profile at this time.'


if __name__ == '__main__':
    mock_app = {
        'phone': '0712345678', 'national_id': '12345678',
        'monthly_income': 55000, 'loan_amount': 100000,
        'employment': 'Employed (Formal)',
    }
    mock_pdf = {
        'tx_count': 95, 'total_in': 168000, 'total_out': 121000,
        'net_flow': 47000, 'utilisation': 0.72,
    }
    print(f"Active provider: {SCORER_PROVIDER}")
    print(json.dumps(compute_score(mock_app, mock_pdf), indent=2))
    print("Provider status:", json.dumps(provider_status(), indent=2))
