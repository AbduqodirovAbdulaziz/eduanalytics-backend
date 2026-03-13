"""
EduAnalytics — Students App Views
Barcha view sinflari: Student, DailyAttendance (bulk), HomeworkSubmission (bulk),
QuizResult (bulk), StudentProgress
"""
from datetime import timedelta

from django.utils import timezone
from django.db import transaction

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import (
    Student, Score,
    DailyAttendance, HomeworkSubmission, QuizResult,
    recalculate_score,
)
from .serializers import (
    StudentSerializer, StudentListSerializer, StudentCreateSerializer,
    DailyAttendanceSerializer, DailyAttendanceCreateSerializer,
    BulkAttendanceSerializer,
    HomeworkSubmissionSerializer, HomeworkSubmissionCreateSerializer,
    BulkHomeworkSerializer,
    QuizResultSerializer, QuizResultCreateSerializer,
    BulkQuizSerializer,
)


# ═══════════════════════════════════════════════════════════════
#  STUDENT VIEWS
# ═══════════════════════════════════════════════════════════════

class StudentListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/students/?group_id=1&course_id=2
    POST /api/v1/students/
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Student.objects.filter(
            group__course__teacher=self.request.user
        ).select_related('group', 'group__course').prefetch_related('score')

        group_id  = self.request.query_params.get('group_id')
        course_id = self.request.query_params.get('course_id')
        if group_id:
            qs = qs.filter(group_id=group_id)
        if course_id:
            qs = qs.filter(group__course_id=course_id)
        return qs

    def get_serializer_class(self):
        return StudentCreateSerializer if self.request.method == 'POST' else StudentListSerializer

    @swagger_auto_schema(
        operation_id='students_list',
        operation_summary="O'quvchilar ro'yxati",
        tags=["👨‍🎓 O'quvchilar"],
        manual_parameters=[
            openapi.Parameter('group_id',  openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
            openapi.Parameter('course_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
        ]
    )
    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        serializer = StudentListSerializer(qs, many=True)
        return Response({'data': serializer.data, 'total': qs.count()})

    @swagger_auto_schema(
        operation_id='students_create',
        operation_summary="O'quvchi qo'shish",
        tags=["👨‍🎓 O'quvchilar"],
        request_body=StudentCreateSerializer
    )
    def create(self, request, *args, **kwargs):
        serializer = StudentCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            student = serializer.save()
            return Response(StudentSerializer(student).data, status=status.HTTP_201_CREATED)
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class StudentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET / PUT / DELETE /api/v1/students/<id>/"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Student.objects.filter(
            group__course__teacher=self.request.user
        ).select_related('group', 'group__course').prefetch_related('score')

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return StudentCreateSerializer
        return StudentSerializer

    @swagger_auto_schema(operation_id='students_get',    tags=["👨‍🎓 O'quvchilar"])
    def retrieve(self, request, *args, **kwargs):
        return Response(StudentSerializer(self.get_object()).data)

    @swagger_auto_schema(operation_id='students_update', tags=["👨‍🎓 O'quvchilar"])
    def update(self, request, *args, **kwargs):
        student = self.get_object()
        serializer = StudentCreateSerializer(
            student, data=request.data, partial=True, context={'request': request}
        )
        if serializer.is_valid():
            return Response(StudentSerializer(serializer.save()).data)
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(operation_id='students_delete', tags=["👨‍🎓 O'quvchilar"])
    def destroy(self, request, *args, **kwargs):
        self.get_object().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ═══════════════════════════════════════════════════════════════
#  DAVOMAT VIEWS
# ═══════════════════════════════════════════════════════════════

class AttendanceListCreateView(APIView):
    """
    GET  /api/v1/students/<student_id>/attendance/   — tarix
    POST /api/v1/students/<student_id>/attendance/   — yozuv qo'shish
    """
    permission_classes = [IsAuthenticated]

    def _get_student(self, student_id, teacher):
        return Student.objects.filter(
            id=student_id, group__course__teacher=teacher
        ).first()

    @swagger_auto_schema(
        operation_id='attendance_list',
        operation_summary='Davomat tarixi',
        tags=['📅 Davomat'],
        manual_parameters=[
            openapi.Parameter('days', openapi.IN_QUERY, type=openapi.TYPE_INTEGER,
                              description='Oxirgi N kun (default: 30)'),
        ]
    )
    def get(self, request, student_id):
        student = self._get_student(student_id, request.user)
        if not student:
            return Response({'error': "O'quvchi topilmadi"}, status=404)

        days = int(request.query_params.get('days', 30))
        since = timezone.now().date() - timedelta(days=days)
        qs = DailyAttendance.objects.filter(
            student=student, date__gte=since
        ).order_by('-date', 'lesson_number')

        total   = qs.count()
        present = qs.filter(is_present=True).count()
        return Response({
            'student_id':   student.id,
            'student_name': student.name,
            'period_days':  days,
            'total_lessons': total,
            'present':      present,
            'absent':       total - present,
            'rate':         round(present / total * 100, 1) if total else 0,
            'data': DailyAttendanceSerializer(qs, many=True).data,
        })

    @swagger_auto_schema(
        operation_id='attendance_create',
        operation_summary='Davomat kiritish (bitta)',
        tags=['📅 Davomat'],
        request_body=DailyAttendanceCreateSerializer
    )
    def post(self, request, student_id):
        student = self._get_student(student_id, request.user)
        if not student:
            return Response({'error': "O'quvchi topilmadi"}, status=404)

        data = {**request.data, 'student': student.id}
        serializer = DailyAttendanceCreateSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            obj = serializer.save()
            return Response(DailyAttendanceSerializer(obj).data, status=status.HTTP_201_CREATED)
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class BulkAttendanceView(APIView):
    """
    POST /api/v1/attendance/bulk/
    Bir guruh uchun bir vaqtda davomat kiritish.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_id='attendance_bulk',
        operation_summary="Guruh uchun davomat (bulk)",
        operation_description=(
            "Bir guruhning barcha o'quvchilari uchun bir kunda davomat kiritish.\n\n"
            "**Misol:**\n```json\n"
            "{\n  \"group_id\": 1,\n  \"date\": \"2025-01-15\",\n  \"lesson_number\": 1,\n"
            "  \"attendances\": [\n"
            "    {\"student_id\": 1, \"is_present\": true},\n"
            "    {\"student_id\": 2, \"is_present\": false, \"is_excused\": true, \"note\": \"Kasal\"}\n"
            "  ]\n}\n```"
        ),
        tags=['📅 Davomat'],
        request_body=BulkAttendanceSerializer
    )
    def post(self, request):
        serializer = BulkAttendanceSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        data          = serializer.validated_data
        group         = data['_group']
        date          = data['date']
        lesson_number = data['lesson_number']

        student_map = {s.id: s for s in group.students.all()}
        created     = []
        updated     = []
        affected_students = set()

        with transaction.atomic():
            for item in data['attendances']:
                student = student_map.get(item['student_id'])
                if not student:
                    continue

                obj, was_created = DailyAttendance.objects.update_or_create(
                    student=student,
                    date=date,
                    lesson_number=lesson_number,
                    defaults={
                        'is_present': item['is_present'],
                        'is_excused': item.get('is_excused', False),
                        'note':       item.get('note', ''),
                    }
                )
                if was_created:
                    created.append(obj.id)
                else:
                    updated.append(obj.id)
                affected_students.add(student)

            # Score har bir o'quvchi uchun yangilanadi (signal orqali amalga oshiriladi)
            # lekin bulk bo'lganligi uchun qo'lda chaqiramiz — signal ham ishlaydi
            # chunki update_or_create → post_save → update_score_on_attendance

        return Response({
            'message':   f"{len(created)} ta yangi, {len(updated)} ta yangilandi",
            'created':   len(created),
            'updated':   len(updated),
            'date':      date,
            'group':     group.name,
        }, status=status.HTTP_201_CREATED)


# ═══════════════════════════════════════════════════════════════
#  UY VAZIFASI VIEWS
# ═══════════════════════════════════════════════════════════════

class HomeworkListCreateView(APIView):
    """
    GET  /api/v1/students/<student_id>/homework/
    POST /api/v1/students/<student_id>/homework/
    """
    permission_classes = [IsAuthenticated]

    def _get_student(self, student_id, teacher):
        return Student.objects.filter(
            id=student_id, group__course__teacher=teacher
        ).first()

    @swagger_auto_schema(
        operation_id='homework_list',
        operation_summary='Uy vazifasi tarixi',
        tags=['📝 Uy vazifasi'],
        manual_parameters=[
            openapi.Parameter('days', openapi.IN_QUERY, type=openapi.TYPE_INTEGER,
                              description='Oxirgi N kun (default: 30)'),
        ]
    )
    def get(self, request, student_id):
        student = self._get_student(student_id, request.user)
        if not student:
            return Response({'error': "O'quvchi topilmadi"}, status=404)

        days  = int(request.query_params.get('days', 30))
        since = timezone.now().date() - timedelta(days=days)
        qs    = HomeworkSubmission.objects.filter(student=student, date__gte=since).order_by('-date')

        total     = qs.count()
        submitted = qs.filter(submitted=True).count()
        avg_pct   = 0.0
        if qs.exists():
            avg_pct = round(
                sum(h.percentage for h in qs) / total, 1
            )

        return Response({
            'student_id':     student.id,
            'student_name':   student.name,
            'period_days':    days,
            'total':          total,
            'submitted':      submitted,
            'not_submitted':  total - submitted,
            'avg_percentage': avg_pct,
            'data': HomeworkSubmissionSerializer(qs, many=True).data,
        })

    @swagger_auto_schema(
        operation_id='homework_create',
        operation_summary='Uy vazifasi kiritish (bitta)',
        tags=['📝 Uy vazifasi'],
        request_body=HomeworkSubmissionCreateSerializer
    )
    def post(self, request, student_id):
        student = self._get_student(student_id, request.user)
        if not student:
            return Response({'error': "O'quvchi topilmadi"}, status=404)

        data = {**request.data, 'student': student.id}
        serializer = HomeworkSubmissionCreateSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            obj = serializer.save()
            return Response(HomeworkSubmissionSerializer(obj).data, status=status.HTTP_201_CREATED)
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class BulkHomeworkView(APIView):
    """
    POST /api/v1/homework/bulk/
    Bir guruh uchun bitta uy vazifasini bir vaqtda kiritish.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_id='homework_bulk',
        operation_summary='Guruh uchun uy vazifasi (bulk)',
        tags=['📝 Uy vazifasi'],
        request_body=BulkHomeworkSerializer
    )
    def post(self, request):
        serializer = BulkHomeworkSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        data      = serializer.validated_data
        group     = data['_group']
        date      = data['date']
        title     = data['title']
        max_score = data['max_score']

        student_map = {s.id: s for s in group.students.all()}
        results     = []

        with transaction.atomic():
            for item in data['students']:
                student = student_map.get(item['student_id'])
                if not student:
                    continue
                obj = HomeworkSubmission.objects.create(
                    student=student,
                    date=date,
                    title=title,
                    max_score=max_score,
                    score=item['score'],
                    submitted=item.get('submitted', True),
                    note=item.get('note', ''),
                )
                results.append({
                    'student_id':   student.id,
                    'student_name': student.name,
                    'score':        obj.score,
                    'percentage':   obj.percentage,
                })

        return Response({
            'message': f"{len(results)} ta o'quvchi uchun uy vazifasi kiritildi",
            'title':   title,
            'date':    date,
            'results': results,
        }, status=status.HTTP_201_CREATED)


# ═══════════════════════════════════════════════════════════════
#  QUIZ / IMTIHON VIEWS
# ═══════════════════════════════════════════════════════════════

class QuizListCreateView(APIView):
    """
    GET  /api/v1/students/<student_id>/quiz/?quiz_type=quiz
    POST /api/v1/students/<student_id>/quiz/
    """
    permission_classes = [IsAuthenticated]

    def _get_student(self, student_id, teacher):
        return Student.objects.filter(
            id=student_id, group__course__teacher=teacher
        ).first()

    @swagger_auto_schema(
        operation_id='quiz_list',
        operation_summary='Quiz / imtihon tarixi',
        tags=['📊 Quiz / Imtihon'],
        manual_parameters=[
            openapi.Parameter('quiz_type', openapi.IN_QUERY, type=openapi.TYPE_STRING,
                              enum=['quiz', 'classwork', 'exam'],
                              description='Filtr: tur bo\'yicha'),
            openapi.Parameter('days', openapi.IN_QUERY, type=openapi.TYPE_INTEGER,
                              description='Oxirgi N kun (default: 90)'),
        ]
    )
    def get(self, request, student_id):
        student = self._get_student(student_id, request.user)
        if not student:
            return Response({'error': "O'quvchi topilmadi"}, status=404)

        days      = int(request.query_params.get('days', 90))
        quiz_type = request.query_params.get('quiz_type')
        since     = timezone.now().date() - timedelta(days=days)
        qs        = QuizResult.objects.filter(student=student, date__gte=since)

        if quiz_type:
            qs = qs.filter(quiz_type=quiz_type)
        qs = qs.order_by('-date')

        avg_pct = 0.0
        if qs.exists():
            avg_pct = round(sum(q.percentage for q in qs) / qs.count(), 1)

        return Response({
            'student_id':     student.id,
            'student_name':   student.name,
            'period_days':    days,
            'total':          qs.count(),
            'avg_percentage': avg_pct,
            'data': QuizResultSerializer(qs, many=True).data,
        })

    @swagger_auto_schema(
        operation_id='quiz_create',
        operation_summary='Quiz / imtihon kiritish (bitta)',
        tags=['📊 Quiz / Imtihon'],
        request_body=QuizResultCreateSerializer
    )
    def post(self, request, student_id):
        student = self._get_student(student_id, request.user)
        if not student:
            return Response({'error': "O'quvchi topilmadi"}, status=404)

        data = {**request.data, 'student': student.id}
        serializer = QuizResultCreateSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            obj = serializer.save()
            return Response(QuizResultSerializer(obj).data, status=status.HTTP_201_CREATED)
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class BulkQuizView(APIView):
    """
    POST /api/v1/quiz/bulk/
    Bir guruh uchun bitta quiz/imtihonni bir vaqtda kiritish.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_id='quiz_bulk',
        operation_summary='Guruh uchun quiz / imtihon (bulk)',
        tags=['📊 Quiz / Imtihon'],
        request_body=BulkQuizSerializer
    )
    def post(self, request):
        serializer = BulkQuizSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        data      = serializer.validated_data
        group     = data['_group']
        results   = []

        student_map = {s.id: s for s in group.students.all()}

        with transaction.atomic():
            for item in data['students']:
                student = student_map.get(item['student_id'])
                if not student:
                    continue
                obj = QuizResult.objects.create(
                    student=student,
                    date=data['date'],
                    quiz_type=data['quiz_type'],
                    topic=data['topic'],
                    max_score=data['max_score'],
                    score=item['score'],
                    note=item.get('note', ''),
                )
                results.append({
                    'student_id':   student.id,
                    'student_name': student.name,
                    'score':        obj.score,
                    'percentage':   obj.percentage,
                })

        return Response({
            'message':   f"{len(results)} ta o'quvchi uchun {data['quiz_type']} kiritildi",
            'topic':     data['topic'],
            'quiz_type': data['quiz_type'],
            'date':      data['date'],
            'results':   results,
        }, status=status.HTTP_201_CREATED)


# ═══════════════════════════════════════════════════════════════
#  PROGRESS VIEW — Frontend grafik uchun
# ═══════════════════════════════════════════════════════════════

class StudentProgressView(APIView):
    """
    GET /api/v1/students/<student_id>/progress/
    O'quvchining vaqt davomidagi rivojlanishini ko'rsatuvchi to'liq ma'lumotlar.
    Frontend grafik uchun mo'ljallangan.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_id='student_progress',
        operation_summary="O'quvchi progress grafigi",
        operation_description=(
            "O'quvchining davomat, uy vazifasi, quiz va imtihon bo'yicha "
            "vaqt o'tishi bilan rivojlanish ma'lumotlari.\n\n"
            "Flutter ilovasida grafik (LineChart) ko'rsatish uchun ishlatiladi."
        ),
        tags=["👨‍🎓 O'quvchilar"],
        manual_parameters=[
            openapi.Parameter('days', openapi.IN_QUERY, type=openapi.TYPE_INTEGER,
                              description='Oxirgi N kun (default: 60)'),
        ]
    )
    def get(self, request, student_id):
        student = Student.objects.filter(
            id=student_id, group__course__teacher=request.user
        ).select_related('group', 'group__course', 'score').first()

        if not student:
            return Response({'error': "O'quvchi topilmadi"}, status=404)

        days  = int(request.query_params.get('days', 60))
        since = timezone.now().date() - timedelta(days=days)

        # --- Davomat tarixi (haftalik agregatsiya) ---
        att_qs = DailyAttendance.objects.filter(
            student=student, date__gte=since
        ).order_by('date')

        att_by_week = {}
        for att in att_qs:
            week = att.date.isocalendar()[1]
            key  = f"{att.date.year}-W{week:02d}"
            if key not in att_by_week:
                att_by_week[key] = {'total': 0, 'present': 0}
            att_by_week[key]['total']   += 1
            att_by_week[key]['present'] += int(att.is_present)

        att_history = [
            {
                'week': k,
                'rate': round(v['present'] / v['total'] * 100, 1) if v['total'] else 0,
                'present': v['present'],
                'total':   v['total'],
            }
            for k, v in sorted(att_by_week.items())
        ]

        # --- Uy vazifasi tarixi ---
        hw_history = [
            {
                'date':       str(h.date),
                'title':      h.title,
                'score':      h.score,
                'max_score':  h.max_score,
                'percentage': h.percentage,
                'submitted':  h.submitted,
            }
            for h in HomeworkSubmission.objects.filter(
                student=student, date__gte=since
            ).order_by('date')
        ]

        # --- Quiz tarixi ---
        quiz_history = [
            {
                'date':       str(q.date),
                'topic':      q.topic,
                'quiz_type':  q.quiz_type,
                'score':      q.score,
                'max_score':  q.max_score,
                'percentage': q.percentage,
            }
            for q in QuizResult.objects.filter(
                student=student, date__gte=since, quiz_type__in=['quiz', 'classwork']
            ).order_by('date')
        ]

        # --- Imtihon tarixi ---
        exam_history = [
            {
                'date':       str(e.date),
                'topic':      e.topic,
                'score':      e.score,
                'max_score':  e.max_score,
                'percentage': e.percentage,
            }
            for e in QuizResult.objects.filter(
                student=student, date__gte=since, quiz_type='exam'
            ).order_by('date')
        ]

        # --- Trendlar ---
        from apps.students.models import _calculate_trends
        trends = _calculate_trends(student)

        # --- Joriy natija ---
        try:
            s = student.score
            current_score = {
                'attendance': s.attendance,
                'homework':   s.homework,
                'quiz':       s.quiz,
                'exam':       s.exam,
                'weighted':   round(
                    s.attendance * 0.2 + s.homework * 0.2 +
                    s.quiz * 0.3 + s.exam * 0.3, 1
                ),
            }
        except Score.DoesNotExist:
            current_score = {'attendance': 0, 'homework': 0, 'quiz': 0, 'exam': 0, 'weighted': 0}

        # --- Xulosa ---
        summary = {
            'total_attendance_records': att_qs.count(),
            'total_homework_records':   HomeworkSubmission.objects.filter(student=student).count(),
            'total_quiz_records':       QuizResult.objects.filter(
                student=student, quiz_type__in=['quiz', 'classwork']
            ).count(),
            'total_exam_records':       QuizResult.objects.filter(
                student=student, quiz_type='exam'
            ).count(),
            'improving': (
                trends['attendance_trend'] > 5 or
                trends['quiz_improvement'] > 5
            ),
            'at_risk': (
                trends['consecutive_absent'] >= 3 or
                current_score['weighted'] < 40
            ),
        }

        return Response({
            'student_id':        student.id,
            'student_name':      student.name,
            'group_name':        student.group.name,
            'course_name':       student.group.course.name,
            'period_days':       days,
            'current_score':     current_score,
            'attendance_history': att_history,
            'homework_history':  hw_history,
            'quiz_history':      quiz_history,
            'exam_history':      exam_history,
            'trends':            trends,
            'summary':           summary,
        })
