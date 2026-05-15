"""
Configuración de PRODUCCIÓN — Railway / Render / cualquier servidor
Hereda de settings.py y sobreescribe solo lo necesario.
"""
from .settings import *
import dj_database_url
import os

# ── Seguridad ──────────────────────────────────────────────────────
DEBUG = False

SECRET_KEY = os.environ.get('SECRET_KEY', SECRET_KEY)

_allowed = os.environ.get(
    'ALLOWED_HOSTS',
    '.railway.app,.up.railway.app,.onrender.com,localhost,127.0.0.1'
).split(',')
# Railway healthcheck usa este host — siempre debe estar permitido
ALLOWED_HOSTS = list(set(_allowed + ['healthcheck.railway.app']))

CSRF_TRUSTED_ORIGINS = [
    f"https://{h}" for h in ALLOWED_HOSTS if h.startswith('.')
    or '.' in h
] + ['http://localhost:5000']

# ── Base de datos ──────────────────────────────────────────────────
# Railway inyecta DATABASE_URL automáticamente
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    }
else:
    # Fallback: SQLite si no hay DATABASE_URL
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR + '/db.sqlite3' if isinstance(BASE_DIR, str) else str(BASE_DIR / 'db.sqlite3'),
        }
    }

# ── Archivos estáticos con WhiteNoise ─────────────────────────────
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL  = '/static/'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# ── HTTPS ──────────────────────────────────────────────────────────
# Railway maneja HTTPS en el edge — no redirigir aquí (rompe el healthcheck)
SECURE_SSL_REDIRECT         = False
CSRF_COOKIE_SECURE          = True
SESSION_COOKIE_SECURE       = True
SECURE_HSTS_SECONDS         = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_PROXY_SSL_HEADER     = ('HTTP_X_FORWARDED_PROTO', 'https')

# ── Cache ──────────────────────────────────────────────────────────
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# ── Email ──────────────────────────────────────────────────────────
EMAIL_BACKEND   = 'django.core.mail.backends.console.EmailBackend'

# ── Logs ───────────────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}
