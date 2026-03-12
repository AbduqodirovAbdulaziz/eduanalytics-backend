"""
PythonAnywhere WSGI konfiguratsiyasi
────────────────────────────────────────────────────────────
PythonAnywhere da bu faylni tahrirlang:
  Web tab → WSGI configuration file

1. YOUR_USERNAME ni o'zingizning username bilan almashtiring
2. Loyiha papkasi yo'lini to'g'rilang
"""
import sys
import os
from dotenv import load_dotenv

# ─── Loyiha joylashuvi ────────────────────────────────────────
# PythonAnywhere da loyiha odatda: /home/YOUR_USERNAME/mysite/
PROJECT_DIR = '/home/eduanalytics/eduanalytics_backend'
VENV_DIR    = '/home/eduanalytics/.virtualenvs/eduanalytics/lib/python3.12/site-packages'

# ─── Virtual environment ─────────────────────────────────────
if VENV_DIR not in sys.path:
    sys.path.insert(0, VENV_DIR)

if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

# ─── .env yuklash ─────────────────────────────────────────────
load_dotenv(os.path.join(PROJECT_DIR, '.env'))

# ─── Django sozlamalar ────────────────────────────────────────
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ['DEBUG'] = 'False'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
