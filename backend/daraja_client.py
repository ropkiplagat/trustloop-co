"""
M-Pesa Daraja API client. Stub until ODPC registration +
Safaricom business approval complete.
Sandbox endpoints at https://sandbox.safaricom.co.ke
Production at https://api.safaricom.co.ke
"""
import os
import base64
import datetime
import requests


class DarajaClient:
    def __init__(self):
        self.env            = os.getenv('DARAJA_ENV', 'sandbox')
        self.consumer_key   = os.getenv('DARAJA_CONSUMER_KEY', '')
        self.consumer_secret = os.getenv('DARAJA_CONSUMER_SECRET', '')
        self.shortcode      = os.getenv('DARAJA_SHORTCODE', '')
        self.passkey        = os.getenv('DARAJA_PASSKEY', '')
        self.callback_url   = os.getenv(
            'DARAJA_CALLBACK_URL',
            'https://trustloopafrica.com/api/daraja/callback'
        )
        self.base_url = (
            'https://api.safaricom.co.ke'
            if self.env == 'production'
            else 'https://sandbox.safaricom.co.ke'
        )

    def is_ready(self) -> bool:
        return bool(
            self.consumer_key and self.consumer_secret
            and self.shortcode and self.passkey
        )

    def get_token(self) -> str:
        if not self.is_ready():
            raise ValueError('Daraja credentials not configured')
        creds = base64.b64encode(
            f'{self.consumer_key}:{self.consumer_secret}'.encode()
        ).decode()
        resp = requests.get(
            f'{self.base_url}/oauth/v1/generate?grant_type=client_credentials',
            headers={'Authorization': f'Basic {creds}'},
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()['access_token']

    def stk_push(self, phone: str, amount: int, reference: str, description: str) -> dict:
        """Initiate M-Pesa STK push. Returns stub if not configured."""
        if not self.is_ready():
            return {
                'stub': True,
                'ready': False,
                'message': 'Daraja not configured — awaiting ODPC registration and Safaricom approval',
                'env': self.env,
            }
        token = self.get_token()
        ts = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode(
            f'{self.shortcode}{self.passkey}{ts}'.encode()
        ).decode()
        payload = {
            'BusinessShortCode': self.shortcode,
            'Password':          password,
            'Timestamp':         ts,
            'TransactionType':   'CustomerPayBillOnline',
            'Amount':            int(amount),
            'PartyA':            phone,
            'PartyB':            self.shortcode,
            'PhoneNumber':       phone,
            'CallBackURL':       self.callback_url,
            'AccountReference':  reference,
            'TransactionDesc':   description,
        }
        resp = requests.post(
            f'{self.base_url}/mpesa/stkpush/v1/processrequest',
            json=payload,
            headers={'Authorization': f'Bearer {token}'},
            timeout=15
        )
        return resp.json()

    def process_callback(self, payload: dict) -> dict:
        """Parse M-Pesa STK push callback payload."""
        try:
            body     = payload.get('Body', {})
            stkcd    = body.get('stkCallback', {})
            code     = stkcd.get('ResultCode', -1)
            desc     = stkcd.get('ResultDesc', '')
            checkout = stkcd.get('CheckoutRequestID', '')
            if code == 0:
                items = {
                    i['Name']: i.get('Value')
                    for i in stkcd.get('CallbackMetadata', {}).get('Item', [])
                }
                return {
                    'success':    True,
                    'checkout_id': checkout,
                    'amount':     items.get('Amount'),
                    'receipt':    items.get('MpesaReceiptNumber'),
                    'phone':      items.get('PhoneNumber'),
                }
            return {'success': False, 'checkout_id': checkout, 'reason': desc}
        except Exception as e:
            return {'success': False, 'reason': str(e)}


if __name__ == '__main__':
    c = DarajaClient()
    print(f'Ready: {c.is_ready()}  Env: {c.env}')
    print(c.stk_push('254712345678', 100, 'TL-TEST', 'TrustLoop test'))
