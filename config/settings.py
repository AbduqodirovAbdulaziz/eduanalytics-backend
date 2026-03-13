"""
EduAnalytics Backend — Django Settings
✅ Xavfsizlik, Jazzmin Admin, Swagger, PythonAnywhere deployment tayyor
"""
import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ══════════════════════════════════════════════════════════════
#  🔐 SECRET KEY
# ══════════════════════════════════════════════════════════════
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise ValueError(
        "⛔ DJANGO_SECRET_KEY topilmadi! .env faylga qo'shing."
    )

DEBUG = os.getenv('DEBUG', 'False') == 'True'

_ALLOWED = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1')
ALLOWED_HOSTS = [h.strip() for h in _ALLOWED.split(',') if h.strip()]

# ══════════════════════════════════════════════════════════════
#  📦 INSTALLED APPS
# ══════════════════════════════════════════════════════════════
INSTALLED_APPS = [
    'jazzmin',                                    # ← birinchi bo'lishi shart!

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'drf_yasg',

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
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',      # ← static fayllar
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
            'NAME':   BASE_DIR / 'db.sqlite3',
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
#  🔑 JWT
# ══════════════════════════════════════════════════════════════
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':    timedelta(hours=int(os.getenv('JWT_EXPIRE_HOURS', 24))),
    'REFRESH_TOKEN_LIFETIME':   timedelta(days=int(os.getenv('JWT_REFRESH_DAYS', 7))),
    'ROTATE_REFRESH_TOKENS':    True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN':        True,
    'AUTH_HEADER_TYPES':        ('Bearer',),
    'USER_ID_FIELD':            'id',
    'USER_ID_CLAIM':            'user_id',
    'ALGORITHM':                'HS256',
    'SIGNING_KEY':              SECRET_KEY,
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
#  🌍 CORS
# ══════════════════════════════════════════════════════════════
CORS_ALLOW_ALL_ORIGINS  = True
CORS_ALLOW_CREDENTIALS  = True
CORS_ALLOW_METHODS      = ['DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT']
CORS_ALLOW_HEADERS      = [
    'accept', 'accept-encoding', 'authorization',
    'content-type', 'dnt', 'origin', 'user-agent',
    'x-csrftoken', 'x-requested-with',
]

# ══════════════════════════════════════════════════════════════
#  🎨 JAZZMIN
# ══════════════════════════════════════════════════════════════
JAZZMIN_SETTINGS = {
    "site_title":        "EduAnalytics Admin",
    "site_header":       "EduAnalytics",
    "site_brand":        "📊 EduAnalytics",
    "welcome_sign":      "EduAnalytics Admin paneliga xush kelibsiz!",
    "copyright":         "EduAnalytics © 2025",
    "site_icon":         None,
    "site_logo":         None,
    "icons": {
        "auth":                   "fas fa-users-cog",
        "authentication.teacher": "fas fa-chalkboard-teacher",
        "courses.course":         "fas fa-book",
        "groups.group":           "fas fa-users",
        "students.student":       "fas fa-user-graduate",
        "students.score":         "fas fa-star",
        "predictions.prediction": "fas fa-brain",
    },
    "default_icon_parents":  "fas fa-folder",
    "default_icon_children": "fas fa-circle",
    "show_sidebar":           True,
    "navigation_expanded":    True,
    "hide_apps":              [],
    "hide_models":            [],
    "search_model":           ["authentication.Teacher", "students.Student"],
    "topmenu_links": [
        {"name": "🏠 Dashboard",  "url": "admin:index"},
        {"name": "📖 Swagger UI", "url": "/api/v1/swagger/", "new_window": True},
        {"name": "🔄 ReDoc API",  "url": "/api/v1/redoc/",  "new_window": True},
    ],
    "usermenu_links":         [{"name": "📊 Dashboard", "url": "admin:index"}],
    "show_ui_builder":        False,
    "changeform_format":      "horizontal_tabs",
    "related_modal_active":   True,
    "use_google_fonts_cdn":   True,
    "custom_css":             None,
    "custom_js":              None,
    "language_chooser":       False,
    "order_with_respect_to":  [
        "authentication", "courses", "groups",
        "students", "predictions", "statistics",
    ],
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text":       False,
    "body_small_text":         False,
    "brand_colour":            "navbar-primary",
    "accent":                  "accent-primary",
    "navbar":                  "navbar-dark",
    "no_navbar_border":        True,
    "navbar_fixed":            True,
    "layout_boxed":            False,
    "sidebar_fixed":           True,
    "sidebar":                 "sidebar-dark-primary",
    "sidebar_nav_child_indent": True,
    "theme":                   "default",
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
#  📝 SWAGGER
# ══════════════════════════════════════════════════════════════
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type':        'apiKey',
            'name':        'Authorization',
            'in':          'header',
            'description': 'JWT Token: Bearer <token>',
        }
    },
    'USE_SESSION_AUTH':         False,
    'JSON_EDITOR':              True,
    'SUPPORTED_SUBMIT_METHODS': ['get', 'post', 'put', 'patch', 'delete'],
    'OPERATIONS_SORTER':        'alpha',
    'DOC_EXPANSION':            'none',
    'DEEP_LINKING':             True,
    'VALIDATOR_URL':            None,
}

REDOC_SETTINGS = {
    'LAZY_RENDERING':   False,
    'EXPAND_RESPONSES': 'all',
}

# ══════════════════════════════════════════════════════════════
#  🔒 PASSWORD VALIDATORS
# ══════════════════════════════════════════════════════════════
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ══════════════════════════════════════════════════════════════
#  🔒 PRODUCTION XAVFSIZLIK
# ══════════════════════════════════════════════════════════════
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER      = True
    SECURE_CONTENT_TYPE_NOSNIFF    = True
    SECURE_HSTS_SECONDS            = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD            = True
    SECURE_SSL_REDIRECT            = False      # PythonAnywhere proxy ishlatadi
    SECURE_PROXY_SSL_HEADER        = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE          = True
    CSRF_COOKIE_SECURE             = True
    X_FRAME_OPTIONS                = 'DENY'

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
STATIC_URL   = '/static/'
STATIC_ROOT  = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = []

# WhiteNoise — production da static fayllarni serve qilish
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ══════════════════════════════════════════════════════════════
#  🤖 ML MODEL
# ══════════════════════════════════════════════════════════════
ML_MODEL_PATH = os.getenv(
    'MODEL_PATH',
    str(BASE_DIR / 'ml' / 'models' / 'model_v2.pkl')
)

# ══════════════════════════════════════════════════════════════
#  📋 LOGGING
# ══════════════════════════════════════════════════════════════
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module}: {message}',
            'style':  '{',
        },
    },
    'handlers': {
        'console': {
            'class':     'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level':    'WARNING',
    },
    'loggers': {
        'django': {
            'handlers':  ['console'],
            'level':     os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'ml': {
            'handlers':  ['console'],
            'level':     'DEBUG',
            'propagate': False,
        },
    },
}
