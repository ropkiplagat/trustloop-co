"""Full end-to-end API test — run on VPS via SFTP+exec."""
import urllib.request, json, time, sys

BASE = 'http://127.0.0.1:5001/api'

def ok(label, val): print(f'  OK  {label}: {val}')
def fail(label, e): print(f'  FAIL {label}: {e}'); sys.exit(1)

# 1. Health
try:
    r = urllib.request.urlopen(f'{BASE}/health', timeout=5)
    ok('Health', json.loads(r.read()).get('status'))
except Exception as e: fail('Health', e)

# 2. Submit application
try:
    payload = json.dumps({
        'full_name':'Abraham Korir','national_id':'34567890',
        'phone':'0712000001','county':'Nairobi',
        'employment':'Employed (Formal)','monthly_income':85000,
        'loan_amount':150000,'loan_purpose':'Business Capital','tenure':'12 Months'
    }).encode()
    req = urllib.request.Request(f'{BASE}/apply', data=payload,
          headers={'Content-Type':'application/json'}, method='POST')
    r   = urllib.request.urlopen(req, timeout=25)
    res = json.loads(r.read())
    ref = res['ref']
    ok('Submit', f"ref={ref} status={res['status']}")
except Exception as e: fail('Submit', e)

# 3. Score
time.sleep(1)
try:
    r  = urllib.request.urlopen(f'{BASE}/score/{ref}', timeout=8)
    sc = json.loads(r.read())
    ok('Score', f"{sc.get('score')}/850 status={sc.get('status')}")
except Exception as e: fail('Score', e)

# 4. List
try:
    r   = urllib.request.urlopen(f'{BASE}/applications?limit=10', timeout=8)
    lst = json.loads(r.read())
    ok('List', f"count={lst['count']}")
except Exception as e: fail('List', e)

# 5. Approve
try:
    payload2 = json.dumps({'status':'Approved'}).encode()
    req2 = urllib.request.Request(f'{BASE}/applications/{ref}/status',
           data=payload2, headers={'Content-Type':'application/json'}, method='PUT')
    r2  = urllib.request.urlopen(req2, timeout=8)
    upd = json.loads(r2.read())
    ok('Approve', upd['status'])
except Exception as e: fail('Approve', e)

print()
print('ALL 5 API TESTS PASSED')
