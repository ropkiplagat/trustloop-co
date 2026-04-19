"""
TrustLoop Credit Scorer
- Mock scorer: computes score from M-Pesa parsed data locally
- SpinMobile hook: plug in API key when Abraham provides it
"""
import os
import json
import math
from datetime import datetime

# ── SpinMobile config (set env var when key is received) ──
SPINMOBILE_API_KEY = os.getenv('SPINMOBILE_API_KEY', '')
SPINMOBILE_BASE    = os.getenv('SPINMOBILE_BASE_URL', 'https://api.spinmobile.co/v1')

SCORE_MIN = 300
SCORE_MAX = 850


def compute_score(application: dict, pdf_data: dict) -> dict:
    """
    Entry point. Uses SpinMobile if key is set, otherwise mock scorer.
    Returns score dict: { score, rating, breakdown, recommendation }
    """
    if SPINMOBILE_API_KEY:
        return _spinmobile_score(application, pdf_data)
    return _mock_score(application, pdf_data)


def _spinmobile_score(application: dict, pdf_data: dict) -> dict:
    """
    Live SpinMobile API call.
    Swap in when Abraham provides the key.
    """
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
        data = resp.json()
        return _normalise_spinmobile(data)
    except Exception as e:
        print(f"[SCORER] SpinMobile error: {e} — falling back to mock")
        return _mock_score(application, pdf_data)


def _normalise_spinmobile(data: dict) -> dict:
    """Normalise SpinMobile response to TrustLoop standard format."""
    score = int(data.get('credit_score', data.get('score', 500)))
    return {
        'score':          score,
        'rating':         _rating(score),
        'breakdown':      data.get('breakdown', {}),
        'recommendation': _recommendation(score),
        'source':         'spinmobile',
        'scored_at':      datetime.now().isoformat(),
    }


def _mock_score(application: dict, pdf_data: dict) -> dict:
    """
    Deterministic mock scorer based on M-Pesa data signals.
    Produces realistic 300–850 scores without an API key.
    """
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

    # 1. Payment history (35%) — proxy: tx frequency
    pay_pts = min(tx_count / 180 * (0.35 * SCORE_MAX), 0.35 * SCORE_MAX)
    breakdown['payment_history'] = round(pay_pts)
    score += pay_pts

    # 2. Income flow (30%) — inflow vs declared income
    if income > 0 and total_in > 0:
        ratio = min(total_in / (income * 3), 1.2)  # 3 months vs declared
        inc_pts = ratio * 0.30 * SCORE_MAX
    else:
        inc_pts = 0.15 * SCORE_MAX  # no income data = average
    breakdown['income_flow'] = round(inc_pts)
    score += inc_pts

    # 3. Credit utilisation (20%) — lower is better
    util_pts = (1 - min(utilisation, 1.0)) * 0.20 * SCORE_MAX
    breakdown['utilisation'] = round(util_pts)
    score += util_pts

    # 4. Loan-to-income ratio (15%) — lower is better
    if income > 0:
        lti = amount / (income * 12)
        lti_pts = max(0, 1 - lti) * 0.15 * SCORE_MAX
    else:
        lti_pts = 0.075 * SCORE_MAX
    breakdown['loan_to_income'] = round(lti_pts)
    score += lti_pts

    # Employment bonus
    emp_bonus = {'Employed (Formal)': 30, 'Self-Employed': 15, 'Farmer': 10, 'Casual Worker': 5}
    score += emp_bonus.get(emp, 0)

    # Net flow bonus
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
    result = compute_score(mock_app, mock_pdf)
    print(json.dumps(result, indent=2))
