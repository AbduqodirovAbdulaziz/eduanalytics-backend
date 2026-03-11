"""
EduAnalytics — Asosiy URL konfiguratsiyasi
Swagger: /api/v1/swagger/
ReDoc:   /api/v1/redoc/
Admin:   /admin/
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# ══════════════════════════════════════════════════════════════
#  📖 SWAGGER / REDOC SOZLAMALAR
# ══════════════════════════════════════════════════════════════
schema_view = get_schema_view(
    openapi.Info(
        title="📊 EduAnalytics API",
        default_version='v1',
        description="""
## EduAnalytics — O'quv Analitika Tizimi API

Bu API Flutter frontend ilovasi bilan ishlash uchun mo'ljallangan.

### 🔐 Autentifikatsiya
1. `POST /api/v1/auth/login` orqali token oling
2. Yuqoridagi **Authorize** tugmasini bosing
3. `Bearer <your-token>` kiriting

### 📚 Asosiy resurslar
| Resurs | Endpoint |
|--------|----------|
| Autentifikatsiya | `/api/v1/auth/` |
| Kurslar | `/api/v1/courses/` |
| Guruhlar | `/api/v1/groups/` |
| O'quvchilar | `/api/v1/students/` |
| ML Prognoz | `/api/v1/predict/` |
| Statistika | `/api/v1/stats/` |

### 🤖 ML Prognoz Darajalari
- **High Performance** (≥70): Yuqori ko'rsatkich
- **Medium Performance** (40–69): O'rta daraja  
- **Low Performance** (<40): Darhol yordam kerak
        """,
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="admin@edu.uz"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    authentication_classes=[],
)

# ══════════════════════════════════════════════════════════════
#  🌐 URL PATTERNS
# ══════════════════════════════════════════════════════════════
urlpatterns = [
    # ── Admin panel (Jazzmin) ──────────────────────────────
    path('admin/', admin.site.urls),

    # ── API v1 ────────────────────────────────────────────
    path('api/v1/', include([

        # Authentication
        path('auth/',    include('apps.authentication.urls')),

        # CRUD
        path('courses/', include('apps.courses.urls')),
        path('groups/',  include('apps.groups.urls')),
        path('students/', include('apps.students.urls')),

        # ML
        path('predict/', include('apps.predictions.urls')),

        # Statistics
        path('stats/',   include('apps.statistics.urls')),

        # ── Swagger & ReDoc ───────────────────────────────
        re_path(r'^swagger(?P<format>\.json|\.yaml)$',
                schema_view.without_ui(cache_timeout=0), name='schema-json'),
        path('swagger/',
             schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
        path('redoc/',
             schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    ])),
]

# Media fayllar (faqat rivojlanish uchun)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
