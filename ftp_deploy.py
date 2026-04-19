"""Deploy static files to SiteGround via FTPS."""
import ftplib, ssl, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HOST  = 'c1100633.sgvps.net'
USER  = 'rop@trustloopafrica.com'
PASS  = 'Bali@2017?!'
LOCAL = os.path.abspath(os.path.dirname(__file__))

UPLOADS = [
    ('index.html',          'public_html/index.html'),
    ('for-saccos.html',     'public_html/for-saccos.html'),
    ('for-lenders.html',    'public_html/for-lenders.html'),
    ('how-it-works.html',   'public_html/how-it-works.html'),
    ('pricing.html',        'public_html/pricing.html'),
    ('about.html',          'public_html/about.html'),
    ('blog.html',           'public_html/blog.html'),
    ('contact.html',        'public_html/contact.html'),
    ('dashboard.html',      'public_html/dashboard.html'),
    ('score.html',          'public_html/score.html'),
    ('.htaccess',           'public_html/.htaccess'),
    ('robots.txt',          'public_html/robots.txt'),
    ('sitemap.xml',         'public_html/sitemap.xml'),
    ('assets/style.css',    'public_html/assets/style.css'),
    ('assets/logo.svg',     'public_html/assets/logo.svg'),
]

def ensure_dir(ftp, path):
    parts = path.split('/')
    for i in range(1, len(parts)):
        d = '/'.join(parts[:i])
        if not d: continue
        try:
            ftp.mkd(d)
        except ftplib.error_perm:
            pass  # already exists

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

ftp = ftplib.FTP_TLS(timeout=30)
ftp.connect(HOST, 21)
ftp.auth()
ftp.prot_p()
ftp.login(USER, PASS)
print(f'Connected to {HOST}')
print('Current dir:', ftp.pwd())

# List root to understand structure
print('Root listing:', ftp.nlst()[:10])

for local_rel, remote_rel in UPLOADS:
    local_path  = os.path.join(LOCAL, local_rel.replace('/', os.sep))
    if not os.path.exists(local_path):
        print(f'SKIP (missing): {local_path}')
        continue
    ensure_dir(ftp, remote_rel)
    with open(local_path, 'rb') as f:
        ftp.storbinary(f'STOR {remote_rel}', f)
    size = os.path.getsize(local_path)
    print(f'UPLOADED: {remote_rel} ({size:,} bytes)')

ftp.quit()
print('DONE — all files uploaded to SiteGround')
