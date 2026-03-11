# 📊 EduAnalytics Backend API

> Django REST Framework + JWT + Jazzmin Admin + Swagger + ML Prognoz

---

## 🚀 Mahalliy Ishga Tushirish

### 1. Loyihani yuklash
```bash
git clone https://github.com/SIZNING_USERNAME/eduanalytics_backend.git
cd eduanalytics_backend
```

### 2. Virtual muhit
```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Linux / Mac:
source venv/bin/activate
```

### 3. Kutubxonalar
```bash
pip install -r requirements.txt
```

### 4. .env fayl yaratish
```bash
# .env.example nusxasini oling:
copy .env.example .env          # Windows
cp .env.example .env            # Linux/Mac

# SECRET_KEY yarating:
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Natijani .env faylga DJANGO_SECRET_KEY ga joylashtiring
```

### 5. Migratsiyalar + Demo ma'lumotlar
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py seed_data          # Demo data (teacher@edu.uz / 123456)
python manage.py createsuperuser    # Admin hisobi
```

### 6. ML modelni o'qitish (ixtiyoriy)
```bash
python ml/train.py
```

### 7. Server
```bash
python manage.py runserver
```

---

## 🔗 Manzillar

| Sahifa | URL |
|--------|-----|
| 🎨 Admin panel (Jazzmin) | http://localhost:8000/admin/ |
| 📖 Swagger UI | http://localhost:8000/api/v1/swagger/ |
| 📋 ReDoc | http://localhost:8000/api/v1/redoc/ |
| 📡 API JSON | http://localhost:8000/api/v1/swagger.json |

---

## 📋 API Endpointlar

**Base URL:** `http://localhost:8000/api/v1`

### 🔐 Autentifikatsiya
```
POST  /auth/login      → JWT token olish
POST  /auth/register   → Ro'yxatdan o'tish
POST  /auth/logout     → Chiqish
GET   /auth/me         → Profil
PUT   /auth/me         → Profilni yangilash
POST  /auth/refresh    → Token yangilash
```

### 📚 Kurslar
```
GET    /courses         → Ro'yxat
POST   /courses         → Yaratish
GET    /courses/:id     → Tafsilot
PUT    /courses/:id     → Yangilash
DELETE /courses/:id     → O'chirish
```

### 👥 Guruhlar
```
GET    /groups?course_id=1  → Ro'yxat
POST   /groups              → Yaratish
GET    /groups/:id          → Tafsilot
PUT    /groups/:id          → Yangilash
DELETE /groups/:id          → O'chirish
```

### 🎓 O'quvchilar
```
GET    /students?page=1&limit=20&group_id=1&course_id=2  → Pagination bilan
POST   /students                                          → Yaratish
GET    /students/:id                                      → Tafsilot
PUT    /students/:id                                      → Yangilash
DELETE /students/:id                                      → O'chirish
```

### 🤖 ML Prognoz
```
POST /predict               → Bitta o'quvchi
POST /predict/batch         → Ko'p o'quvchilar
GET  /predict/history/:id   → Tarix
```

### 📊 Statistika
```
GET /stats/overview           → Umumiy ko'rsatkichlar
GET /stats/courses/:id        → Kurs statistikasi
GET /stats/at-risk            → Xavf ostidagi o'quvchilar
```

---

## ☁️ Bepul Serverga Deploy Qilish

### 🔴 Railway (Eng oson — tavsiya etiladi)
1. https://railway.app da hisob oching
2. GitHub reponi ulang
3. PostgreSQL qo'shing (Add plugin)
4. Environment Variables sozlang:
   ```
   DJANGO_SECRET_KEY = <generatsiya qiling>
   DEBUG = False
   USE_SQLITE = False
   DATABASE_URL = <Railway PostgreSQL URL — avtomatik to'ldiriladi>
   ALLOWED_HOSTS = yourapp.railway.app
   ```
5. Deploy tugmasini bosing — tayyor!

### 🟢 PythonAnywhere (Django uchun qulay)
1. https://pythonanywhere.com da Free hisob oching
2. Bash console ochib:
   ```bash
   git clone https://github.com/SIZNING/eduanalytics_backend
   cd eduanalytics_backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   # .env faylni nano bilan tahrirlang
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```
3. Web tab → Add new web app → Manual config → Python 3.11
4. WSGI file ni `pythonanywhere_wsgi.py` dagi kodni nusxalab qo'ying
5. Static files: `/static/` → `/home/USER/eduanalytics_backend/staticfiles/`
6. Reload → tayyor!

### 🔵 Render (render.com)
1. https://render.com da hisob oching
2. New Web Service → GitHub reponi tanlang
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn config.wsgi:application`
5. PostgreSQL Add-on qo'shing
6. Environment variables qo'shing

---

## 🔑 Demo Login
```
Email:  teacher@edu.uz
Parol:  123456
```

## 🤖 ML Prognoz Misol (curl)
```bash
# 1. Token oling
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "teacher@edu.uz", "password": "123456"}'

# 2. Prognoz qiling
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"student_id": 1, "attendance": 45, "homework": 38, "quiz": 42, "exam": 35}'
```

---

## 🏗️ Loyiha Tuzilmasi
```
eduanalytics_backend/
├── apps/
│   ├── authentication/     # Teacher + JWT
│   ├── courses/            # Kurslar
│   ├── groups/             # Guruhlar
│   ├── students/           # O'quvchilar + Natijalar
│   ├── predictions/        # ML prognoz
│   └── statistics/         # Statistika
├── config/
│   ├── settings.py         # ✅ Jazzmin, Swagger, xavfsizlik
│   ├── urls.py             # ✅ Swagger UI ulangan
│   └── pagination.py
├── ml/
│   ├── ml_service.py       # Weighted formula + sklearn
│   ├── train.py            # Model o'qitish
│   └── models/             # .pkl fayllar
├── .env                    # ⚠️ GitHubga yuklamang!
├── .env.example            # ✅ Template
├── .gitignore              # ✅
├── Procfile                # Railway/Render
├── railway.toml            # Railway config
├── pythonanywhere_wsgi.py  # PythonAnywhere config
├── runtime.txt             # Python versiyasi
├── manage.py
└── requirements.txt
```
