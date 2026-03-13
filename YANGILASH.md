# EduAnalytics — Yangilash buyruqlari
# Loyiha joyida terminalda ketma-ket ishlating:

# 1. Loyiha papkasiga o'tish
cd D:\PYTHON LOYIHALAR\EDU_ANALYTICS\eduanalytics_backend

# 2. Migration bajarish (yangi jadvallar yaratiladi)
python manage.py migrate

# 3. (Ixtiyoriy) Yangi ML model o'qitish
python ml/train.py

# 4. Serverni qayta ishga tushirish
python manage.py runserver

# ── Yangi endpointlar ────────────────────────────────────────────
# Bitta o'quvchi uchun:
#   GET/POST  /api/v1/students/<id>/attendance/
#   GET/POST  /api/v1/students/<id>/homework/
#   GET/POST  /api/v1/students/<id>/quiz/
#   GET       /api/v1/students/<id>/progress/

# Guruh uchun (bulk):
#   POST      /api/v1/attendance/bulk/
#   POST      /api/v1/homework/bulk/
#   POST      /api/v1/quiz/bulk/

# ── Bulk attendance misoli ───────────────────────────────────────
# POST /api/v1/attendance/bulk/
# {
#   "group_id": 1,
#   "date": "2025-01-15",
#   "lesson_number": 1,
#   "attendances": [
#     {"student_id": 1, "is_present": true},
#     {"student_id": 2, "is_present": false, "is_excused": true, "note": "Kasal"}
#   ]
# }

# ── Bulk homework misoli ─────────────────────────────────────────
# POST /api/v1/homework/bulk/
# {
#   "group_id": 1,
#   "date": "2025-01-15",
#   "title": "3.1-mashq: Kvadrat tenglamalar",
#   "max_score": 10,
#   "students": [
#     {"student_id": 1, "score": 9, "submitted": true},
#     {"student_id": 2, "score": 0, "submitted": false, "note": "Topshirmadi"}
#   ]
# }

# ── Bulk quiz misoli ─────────────────────────────────────────────
# POST /api/v1/quiz/bulk/
# {
#   "group_id": 1,
#   "date": "2025-01-20",
#   "quiz_type": "quiz",
#   "topic": "Kvadrat tenglamalar",
#   "max_score": 20,
#   "students": [
#     {"student_id": 1, "score": 17},
#     {"student_id": 2, "score": 8}
#   ]
# }
