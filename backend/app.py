"""
TrustLoop Flask API
Serves: borrower intake, score retrieval, admin dashboard data, CSV export
"""
import os
import json
import random
import string
from datetime import datetime
from flask import (
    Flask, request, jsonify, send_from_directory,
    abort, after_this_request
)
from werkzeug.utils import secure_filename

# ── Local modules ──
from db      import init_db, insert_application, update_score, update_status, get_application, list_applications
from parser  import parse_mpesa_pdf
from scorer  import compute_score
from notify  import notify_submission, notify_score_ready

# ── App setup ──
BASE_DIR    = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
UPLOAD_DIR  = os.path.join(BASE_DIR, 'uploads')
STATIC_DIR  = BASE_DIR

os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path='/trustloop')
app.config['MAX_CONTENT_LENGTH'] = 12 * 1024 * 1024  # 12MB max upload

ALLOWED_EXTENSIONS = {'pdf'}


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_ref() -> str:
    return 'TL-' + ''.join(random.choices(string.digits, k=6))


def cors(response):
    response.headers['Access-Control-Allow-Origin']  = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,OPTIONS'
    return response


@app.after_request
def add_cors(response):
    return cors(response)


@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum 10MB.'}), 413


# ──────────────────────────────────────────────
# Static HTML pages
# ──────────────────────────────────────────────

@app.route('/trustloop/')
@app.route('/trustloop/index.html')
def index():
    return send_from_directory(STATIC_DIR, 'index.html')


@app.route('/trustloop/dashboard.html')
def dashboard():
    return send_from_directory(STATIC_DIR, 'dashboard.html')


@app.route('/trustloop/score.html')
def score_page():
    return send_from_directory(STATIC_DIR, 'score.html')


@app.route('/trustloop/assets/<path:filename>')
def assets(filename):
    return send_from_directory(os.path.join(STATIC_DIR, 'assets'), filename)


# ──────────────────────────────────────────────
# API — Application submission
# ──────────────────────────────────────────────

@app.route('/api/apply', methods=['POST', 'OPTIONS'])
def apply():
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    # Accept multipart/form-data (file upload) or JSON
    if request.content_type and 'multipart' in request.content_type:
        data     = request.form.to_dict()
        pdf_file = request.files.get('mpesaFile')
    else:
        data     = request.get_json(force=True) or {}
        pdf_file = None

    # Required field validation
    required = ['full_name', 'national_id', 'phone', 'loan_amount']
    missing  = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'error': f'Missing fields: {", ".join(missing)}'}), 400

    # Save PDF
    pdf_path = None
    if pdf_file and allowed_file(pdf_file.filename):
        filename = secure_filename(pdf_file.filename)
        ref_tmp  = generate_ref()
        pdf_path = os.path.join(UPLOAD_DIR, f'{ref_tmp}_{filename}')
        pdf_file.save(pdf_path)
    elif pdf_file:
        return jsonify({'error': 'Only PDF files are accepted.'}), 400

    ref = generate_ref()

    application = {
        'ref':            ref,
        'full_name':      data.get('full_name', '').strip(),
        'national_id':    data.get('national_id', '').strip(),
        'phone':          data.get('phone', '').strip(),
        'dob':            data.get('dob', ''),
        'county':         data.get('county', ''),
        'employment':     data.get('employment', ''),
        'employer':       data.get('employer', ''),
        'monthly_income': float(data.get('monthly_income', 0) or 0),
        'loan_amount':    float(data.get('loan_amount', 0)),
        'loan_purpose':   data.get('loan_purpose', ''),
        'tenure':         data.get('tenure', ''),
        'pdf_path':       pdf_path or '',
    }

    try:
        insert_application(application)
    except Exception as e:
        return jsonify({'error': f'Database error: {e}'}), 500

    # Background scoring (synchronous for now — move to Celery in v2)
    try:
        pdf_data     = parse_mpesa_pdf(pdf_path) if pdf_path else {}
        score_result = compute_score(application, pdf_data)
        score_json   = json.dumps(score_result)
        status       = 'Approved' if score_result['score'] >= 700 else \
                       'Reviewing' if score_result['score'] >= 580 else 'Rejected'
        update_score(ref, score_result['score'], score_json, status)
        notify_submission(application)
        notify_score_ready(application, score_result)
    except Exception as e:
        print(f"[APP] Scoring/notify error for {ref}: {e}")

    return jsonify({
        'ref':     ref,
        'status':  'received',
        'message': 'Application submitted. Check your phone for score in 2hrs.',
    }), 201


# ──────────────────────────────────────────────
# API — Score retrieval
# ──────────────────────────────────────────────

@app.route('/api/score/<ref>', methods=['GET'])
def get_score(ref):
    app_data = get_application(ref.upper())
    if not app_data:
        return jsonify({'error': 'Application not found'}), 404

    score_data = {}
    if app_data.get('score_data'):
        try:
            score_data = json.loads(app_data['score_data'])
        except Exception:
            pass

    return jsonify({
        'ref':        app_data['ref'],
        'full_name':  app_data['full_name'],
        'score':      app_data['score'],
        'status':     app_data['status'],
        'score_data': score_data,
        'created_at': app_data['created_at'],
    })


# ──────────────────────────────────────────────
# API — Admin: list applications
# ──────────────────────────────────────────────

@app.route('/api/applications', methods=['GET'])
def get_applications():
    status = request.args.get('status')
    limit  = int(request.args.get('limit', 200))
    rows   = list_applications(status=status, limit=limit)

    # Don't leak pdf_path to frontend
    for r in rows:
        r.pop('pdf_path', None)
        r.pop('score_data', None)

    return jsonify({'applications': rows, 'count': len(rows)})


# ──────────────────────────────────────────────
# API — Admin: update status
# ──────────────────────────────────────────────

@app.route('/api/applications/<ref>/status', methods=['PUT', 'OPTIONS'])
def set_status(ref):
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    body      = request.get_json(force=True) or {}
    new_status = body.get('status')
    allowed    = {'Pending', 'Reviewing', 'Approved', 'Rejected'}

    if new_status not in allowed:
        return jsonify({'error': f'Status must be one of: {", ".join(allowed)}'}), 400

    app_data = get_application(ref.upper())
    if not app_data:
        return jsonify({'error': 'Not found'}), 404

    update_status(ref.upper(), new_status)

    if new_status in ('Approved', 'Rejected') and app_data.get('score_data'):
        try:
            score_result = json.loads(app_data['score_data'])
            notify_score_ready(app_data, score_result)
        except Exception:
            pass

    return jsonify({'ref': ref, 'status': new_status})


# ──────────────────────────────────────────────
# API — Admin: CSV export
# ──────────────────────────────────────────────

@app.route('/api/applications/export', methods=['GET'])
def export_csv():
    import csv
    import io

    rows = list_applications()
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        'ref','full_name','phone','national_id','county','employment',
        'monthly_income','loan_amount','loan_purpose','tenure',
        'score','status','created_at'
    ], extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)

    from flask import Response
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=trustloop-applications.csv'}
    )


# ──────────────────────────────────────────────
# Health check
# ──────────────────────────────────────────────

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'app':    'TrustLoop',
        'time':   datetime.now().isoformat(),
    })


# ──────────────────────────────────────────────
# Boot
# ──────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    port = int(os.getenv('PORT', 5001))
    print(f"[TrustLoop] Starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
