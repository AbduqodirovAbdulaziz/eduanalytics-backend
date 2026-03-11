from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Avg, Count
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.courses.models import Course
from apps.groups.models import Group
from apps.students.models import Student, Score
from apps.predictions.models import Prediction


class OverviewStatsView(APIView):
    """Umumiy statistika ko'rsatkichlari"""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_id='stats_overview',
        operation_summary='Umumiy statistika',
        tags=['📊 Statistika'],
        responses={200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'total_courses':            openapi.Schema(type=openapi.TYPE_INTEGER),
                'total_groups':             openapi.Schema(type=openapi.TYPE_INTEGER),
                'total_students':           openapi.Schema(type=openapi.TYPE_INTEGER),
                'at_risk_students':         openapi.Schema(type=openapi.TYPE_INTEGER),
                'average_score':            openapi.Schema(type=openapi.TYPE_NUMBER),
                'performance_distribution': openapi.Schema(type=openapi.TYPE_OBJECT),
            }
        )}
    )
    def get(self, request):
        teacher = request.user

        total_courses  = Course.objects.filter(teacher=teacher).count()
        total_groups   = Group.objects.filter(course__teacher=teacher).count()
        total_students = Student.objects.filter(group__course__teacher=teacher).count()

        avg = Score.objects.filter(
            student__group__course__teacher=teacher
        ).aggregate(avg=Avg('exam'))

        # ✅ BUG FIX: distinct('field') PostgreSQL-only.
        # SQLite ham ishlashi uchun Python dict ishlatamiz
        student_ids = Student.objects.filter(
            group__course__teacher=teacher
        ).values_list('id', flat=True)

        latest_preds = {}
        for pred in Prediction.objects.filter(
            student_id__in=student_ids
        ).order_by('student_id', '-predicted_at'):
            if pred.student_id not in latest_preds:
                latest_preds[pred.student_id] = pred.level

        perf = {'High Performance': 0, 'Medium Performance': 0, 'Low Performance': 0}
        for level in latest_preds.values():
            if level in perf:
                perf[level] += 1

        return Response({
            'total_courses':            total_courses,
            'total_groups':             total_groups,
            'total_students':           total_students,
            'at_risk_students':         perf.get('Low Performance', 0),
            'average_score':            round(avg.get('avg') or 0.0, 1),
            'performance_distribution': perf,
        })


class CourseStatsView(APIView):
    """Kurs bo'yicha batafsil statistika"""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_id='stats_course',
        operation_summary='Kurs statistikasi',
        tags=['📊 Statistika'],
        manual_parameters=[
            openapi.Parameter('course_id', openapi.IN_PATH, type=openapi.TYPE_INTEGER,
                              description='Kurs ID si')
        ]
    )
    def get(self, request, course_id):
        try:
            course = Course.objects.get(id=course_id, teacher=request.user)
        except Course.DoesNotExist:
            return Response(
                {'error': {'code': 404, 'message': 'Kurs topilmadi yoki ruxsatsiz'}},
                status=404
            )

        groups = Group.objects.filter(course=course).annotate(s_count=Count('students'))
        groups_data = []
        for group in groups:
            scores = Score.objects.filter(student__group=group)
            avg    = scores.aggregate(
                avg_attendance=Avg('attendance'),
                avg_homework=Avg('homework'),
                avg_quiz=Avg('quiz'),
                avg_exam=Avg('exam'),
            )
            groups_data.append({
                'group_id':       group.id,
                'group_name':     group.name,
                'student_count':  group.s_count,
                'avg_attendance': round(avg['avg_attendance'] or 0, 1),
                'avg_homework':   round(avg['avg_homework']   or 0, 1),
                'avg_quiz':       round(avg['avg_quiz']       or 0, 1),
                'avg_exam':       round(avg['avg_exam']       or 0, 1),
            })

        # ✅ BUG FIX: Python dict bilan har student uchun oxirgi prognoz
        student_ids = Student.objects.filter(
            group__course=course
        ).values_list('id', flat=True)

        latest_preds = {}
        for pred in Prediction.objects.filter(
            student_id__in=student_ids
        ).order_by('student_id', '-predicted_at'):
            if pred.student_id not in latest_preds:
                latest_preds[pred.student_id] = pred.level

        perf = {'High Performance': 0, 'Medium Performance': 0, 'Low Performance': 0}
        for level in latest_preds.values():
            if level in perf:
                perf[level] += 1

        return Response({
            'course_id':                course.id,
            'course_name':              course.name,
            'total_students':           len(student_ids),
            'groups':                   groups_data,
            'performance_distribution': perf,
        })


class AtRiskStudentsView(APIView):
    """Xavf ostidagi o'quvchilar ro'yxati (Low Performance)"""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_id='stats_at_risk',
        operation_summary="Xavf ostidagi o'quvchilar",
        tags=['📊 Statistika'],
    )
    def get(self, request):
        teacher = request.user

        student_ids = Student.objects.filter(
            group__course__teacher=teacher
        ).values_list('id', flat=True)

        # ✅ BUG FIX: har bir student uchun faqat oxirgi prognoz
        latest_preds = {}
        for pred in Prediction.objects.filter(
            student_id__in=student_ids
        ).select_related(
            'student', 'student__group', 'student__group__course'
        ).order_by('student_id', '-predicted_at'):
            if pred.student_id not in latest_preds:
                latest_preds[pred.student_id] = pred

        at_risk_data = [
            {
                'student_id':      p.student.id,
                'student_name':    p.student.name,
                'group_name':      p.student.group.name,
                'course_name':     p.student.group.course.name,
                'risk_percentage': p.risk_percentage,
                'predicted_score': p.predicted_score,
                'recommendation':  p.recommendation,
                'predicted_at':    p.predicted_at,
            }
            for p in latest_preds.values()
            if p.level == 'Low Performance'
        ]

        at_risk_data.sort(key=lambda x: x['risk_percentage'], reverse=True)

        return Response({'data': at_risk_data, 'total': len(at_risk_data)})


class GroupStatsView(APIView):
    """Guruh bo'yicha statistika"""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_id='stats_group',
        operation_summary='Guruh statistikasi',
        tags=['📊 Statistika'],
        manual_parameters=[
            openapi.Parameter('group_id', openapi.IN_PATH, type=openapi.TYPE_INTEGER)
        ]
    )
    def get(self, request, group_id):
        try:
            group = Group.objects.get(id=group_id, course__teacher=request.user)
        except Group.DoesNotExist:
            return Response(
                {'error': {'code': 404, 'message': 'Guruh topilmadi'}},
                status=404
            )

        students = Student.objects.filter(group=group).select_related('score')
        student_data = []
        for student in students:
            try:
                s   = student.score
                avg = round((s.attendance + s.homework + s.quiz + s.exam) / 4, 1)
            except Exception:
                s   = None
                avg = 0.0

            latest_pred = Prediction.objects.filter(
                student=student
            ).order_by('-predicted_at').first()

            student_data.append({
                'student_id':      student.id,
                'student_name':    student.name,
                'avg_score':       avg,
                'scores': {
                    'attendance': s.attendance if s else 0,
                    'homework':   s.homework   if s else 0,
                    'quiz':       s.quiz       if s else 0,
                    'exam':       s.exam       if s else 0,
                },
                'level':           latest_pred.level           if latest_pred else None,
                'predicted_score': latest_pred.predicted_score if latest_pred else None,
                'risk_percentage': latest_pred.risk_percentage if latest_pred else None,
            })

        return Response({
            'group_id':       group.id,
            'group_name':     group.name,
            'course_name':    group.course.name,
            'total_students': len(student_data),
            'students':       student_data,
        })
