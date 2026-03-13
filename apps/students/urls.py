from django.urls import path
from .views import (
    StudentListCreateView, StudentDetailView,
    AttendanceListCreateView, BulkAttendanceView,
    HomeworkListCreateView, BulkHomeworkView,
    QuizListCreateView, BulkQuizView,
    StudentProgressView,
)

urlpatterns = [
    # ── O'quvchilar ───────────────────────────────────────────────
    path('',          StudentListCreateView.as_view(), name='student-list'),
    path('<int:pk>/', StudentDetailView.as_view(),     name='student-detail'),

    # ── O'quvchi bo'yicha kunlik ma'lumotlar ──────────────────────
    path('<int:student_id>/attendance/', AttendanceListCreateView.as_view(), name='student-attendance'),
    path('<int:student_id>/homework/',   HomeworkListCreateView.as_view(),   name='student-homework'),
    path('<int:student_id>/quiz/',       QuizListCreateView.as_view(),       name='student-quiz'),
    path('<int:student_id>/progress/',   StudentProgressView.as_view(),      name='student-progress'),
]
