"""
EduAnalytics Backend — Django Settings
✅ Xavfsizlik, Jazzmin Admin, Swagger, Deployment tayyor
"""
import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# .env faylni yuklash
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ══════════════════════════════════════════════════════════════
#  🔐 XAVFSIZLIK — SECRET KEY
#  .env fayldan olinadi. Hech qachon hardcode qilmang!
# ══════════════════════════════════════════════════════════════
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise ValueError(
        "⛔ DJANGO_SECRET_KEY topilmadi!\n"
        "   .env faylingizda DJANGO_SECRET_KEY o'zgaruvchisini qo'shing.\n"
        "   Yaratish uchun: python -c \"from django.core.management.utils import "
        "get_random_secret_key; print(get_random_secret_key())\""
    )

DEBUG = os.getenv('DEBUG', 'True') == 'True'

# ALLOWED_HOSTS — .env dan vergul bilan ajratilgan ro'yxat
_ALLOWED = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1')
ALLOWED_HOSTS = [h.strip() for h in _ALLOWED.split(',') if h.strip()]

# ══════════════════════════════════════════════════════════════
#  📦 INSTALLED APPS
# ══════════════════════════════════════════════════════════════
INSTALLED_APPS = [
    # 🎨 Jazzmin — Django Admin chiroyli interfeys (BIRINCHI bo'lishi shart!)
    'jazzmin',

    # Django core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'drf_yasg',           # Swagger UI

    # Local apps
    'apps.authentication',
    'apps.courses',
    'apps.groups',
    'apps.students',
    'apps.predictions',
    'apps.statistics',
]

# ══════════════════════════════════════════════════════════════
#  🔧 MIDDLEWARE
# ══════════════════════════════════════════════════════════════
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',          # CORS — birinchi!
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',      # Static fayllar
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ══════════════════════════════════════════════════════════════
#  🗄️ DATABASE
# ══════════════════════════════════════════════════════════════
USE_SQLITE = os.getenv('USE_SQLITE', 'True') == 'True'

if USE_SQLITE:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(
            default=os.getenv('DATABASE_URL'),
            conn_max_age=600,
            ssl_require=not DEBUG,
        )
    }

# ══════════════════════════════════════════════════════════════
#  👤 CUSTOM USER MODEL
# ══════════════════════════════════════════════════════════════
AUTH_USER_MODEL = 'authentication.Teacher'

# ══════════════════════════════════════════════════════════════
#  🔑 JWT SOZLAMALAR
# ══════════════════════════════════════════════════════════════
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':  timedelta(hours=int(os.getenv('JWT_EXPIRE_HOURS', 24))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.getenv('JWT_REFRESH_DAYS', 7))),
    'ROTATE_REFRESH_TOKENS':  True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN':      True,
    'AUTH_HEADER_TYPES':      ('Bearer',),
    'USER_ID_FIELD':          'id',
    'USER_ID_CLAIM':          'user_id',
    'ALGORITHM':              'HS256',
    'SIGNING_KEY':            SECRET_KEY,
}

# ══════════════════════════════════════════════════════════════
#  🌐 REST FRAMEWORK
# ══════════════════════════════════════════════════════════════
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'config.pagination.StandardPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
    },
}

# ══════════════════════════════════════════════════════════════
#  🌍 CORS SOZLAMALAR
# ══════════════════════════════════════════════════════════════
CORS_ALLOW_ALL_ORIGINS = True
# _CORS = os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:3000')
# CORS_ALLOWED_ORIGINS = [o.strip() for o in _CORS.split(',') if o.strip()]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ['DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT']
CORS_ALLOW_HEADERS = [
    'accept', 'accept-encoding', 'authorization',
    'content-type', 'dnt', 'origin', 'user-agent',
    'x-csrftoken', 'x-requested-with',
]

# ══════════════════════════════════════════════════════════════
#  🎨 JAZZMIN — ADMIN PANEL SOZLAMALAR
# ══════════════════════════════════════════════════════════════
JAZZMIN_SETTINGS = {
    # ── Sarlavha va brendlash ──────────────────────────────
    "site_title":        "EduAnalytics Admin",
    "site_header":       "EduAnalytics",
    "site_brand":        "📊 EduAnalytics",
    "welcome_sign":      "EduAnalytics Admin paneliga xush kelibsiz!",
    "copyright":         "EduAnalytics © 2025",

    # ── Ikonkalar ─────────────────────────────────────────
    "site_icon":         None,
    "site_logo":         None,

    # ── Menyu ikonkalari ──────────────────────────────────
    "icons": {
        "auth":                           "fas fa-users-cog",
        "authentication.teacher":         "fas fa-chalkboard-teacher",
        "courses.course":                 "fas fa-book",
        "groups.group":                   "fas fa-users",
        "students.student":               "fas fa-user-graduate",
        "students.score":                 "fas fa-star",
        "predictions.prediction":         "fas fa-brain",
    },
    "default_icon_parents": "fas fa-folder",
    "default_icon_children": "fas fa-circle",

    # ── Navigatsiya ───────────────────────────────────────
    "show_sidebar":            True,
    "navigation_expanded":     True,
    "hide_apps":               [],
    "hide_models":             [],

    # ── Qidirish ──────────────────────────────────────────
    "search_model": ["authentication.Teacher", "students.Student"],

    # ── UI sozlamalari ────────────────────────────────────
    "topmenu_links": [
        {"name": "🏠 Bosh sahifa", "url": "admin:index"},
        {"name": "📖 API Docs",    "url": "/api/v1/swagger/", "new_window": True},
        {"name": "🔄 ReDoc",       "url": "/api/v1/redoc/",   "new_window": True},
    ],
    "usermenu_links": [
        {"name": "📊 Dashboard", "url": "admin:index"},
    ],

    # ── Tema ──────────────────────────────────────────────
    "show_ui_builder":         False,
    "changeform_format":       "horizontal_tabs",
    "changeform_format_overrides": {
        "auth.user":  "collapsible",
        "auth.group": "vertical_tabs",
    },

    # ── Related modal ─────────────────────────────────────
    "related_modal_active": True,
    "use_google_fonts_cdn":  True,

    # ── Custom CSS/JS ─────────────────────────────────────
    "custom_css": None,
    "custom_js":  None,
    "language_chooser": False,

    # ── Order sidebar ─────────────────────────────────────
    "order_with_respect_to": [
        "authentication",
        "courses",
        "groups",
        "students",
        "predictions",
        "statistics",
    ],
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text":    False,
    "footer_small_text":    False,
    "body_small_text":      False,
    "brand_small_text":     False,
    "brand_colour":         "navbar-primary",
    "accent":               "accent-primary",
    "navbar":               "navbar-dark",
    "no_navbar_border":     True,
    "navbar_fixed":         True,
    "layout_boxed":         False,
    "footer_fixed":         False,
    "sidebar_fixed":        True,
    "sidebar":              "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme":                "default",
    "dark_mode_theme":      None,
    "button_classes": {
        "primary":   "btn-primary",
        "secondary": "btn-secondary",
        "info":      "btn-info",
        "warning":   "btn-warning",
        "danger":    "btn-danger",
        "success":   "btn-success",
    },
}

# ══════════════════════════════════════════════════════════════
#  📝 SWAGGER (drf-yasg) SOZLAMALAR
# ══════════════════════════════════════════════════════════════
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type':        'apiKey',
            'name':        'Authorization',
            'in':          'header',
            'description': 'JWT Token: **Bearer &lt;token&gt;**',
        }
    },
    'USE_SESSION_AUTH':            False,
    'JSON_EDITOR':                 True,
    'SUPPORTED_SUBMIT_METHODS':    ['get', 'post', 'put', 'patch', 'delete'],
    'OPERATIONS_SORTER':           'alpha',
    'TAGS_SORTER':                 'alpha',
    'DOC_EXPANSION':               'none',
    'DEFAULT_MODEL_RENDERING':     'example',
    'DEEP_LINKING':                True,
    'SHOW_EXTENSIONS':             True,
    'SHOW_COMMON_EXTENSIONS':      True,
    'VALIDATOR_URL':               None,
}

REDOC_SETTINGS = {
    'LAZY_RENDERING':  False,
    'HIDE_HOSTNAME':   False,
    'EXPAND_RESPONSES': 'all',
}

# ══════════════════════════════════════════════════════════════
#  🔒 XAVFSIZLIK SOZLAMALAR (Production uchun)
# ══════════════════════════════════════════════════════════════
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Production xavfsizlik sozlamalari
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER        = True
    SECURE_CONTENT_TYPE_NOSNIFF      = True
    SECURE_HSTS_SECONDS              = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS   = True
    SECURE_HSTS_PRELOAD              = True
    # ⚠️ PythonAnywhere HTTPS ni proxy orqali boshqaradi
    # SECURE_SSL_REDIRECT = True qilsak infinite loop bo'ladi!
    SECURE_SSL_REDIRECT              = False
    SECURE_PROXY_SSL_HEADER          = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE            = True
    CSRF_COOKIE_SECURE               = True
    X_FRAME_OPTIONS                  = 'DENY'

# ══════════════════════════════════════════════════════════════
#  🌍 INTERNATIONALIZATION
# ══════════════════════════════════════════════════════════════
LANGUAGE_CODE = 'uz'
TIME_ZONE     = 'Asia/Tashkent'
USE_I18N      = True
USE_TZ        = True

# ══════════════════════════════════════════════════════════════
#  📁 STATIC & MEDIA FILES
# ══════════════════════════════════════════════════════════════
STATIC_URL      = '/static/'
STATIC_ROOT     = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = []

# WhiteNoise — static fayllarni production da serve qilish
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ══════════════════════════════════════════════════════════════
#  🤖 ML MODEL
# ══════════════════════════════════════════════════════════════
ML_MODEL_PATH = os.getenv('MODEL_PATH', str(BASE_DIR / 'ml' / 'models' / 'model_v1.pkl'))

# ══════════════════════════════════════════════════════════════
#  📋 LOGGING
# ══════════════════════════════════════════════════════════════
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'ml': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
