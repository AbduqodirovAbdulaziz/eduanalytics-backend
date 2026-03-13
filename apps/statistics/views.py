from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Avg, Count, Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.courses.models import Course
from apps.groups.models import Group
from apps.students.models import Student, Score
from apps.predictions.models import Prediction


def _latest_predictions_by_student(student_ids):
    """
    Berilgan student_ids uchun har biri bo'yicha eng oxirgi Prediction ni qaytaradi.
    dict: {student_id: Prediction}
    """
    latest = {}
    for pred in Prediction.objects.filter(
        student_id__in=student_ids
    ).order_by('student_id', '-predicted_at'):
        if pred.student_id not in latest:
            latest[pred.student_id] = pred
    return latest


def _performance_distribution(latest_preds: dict) -> dict:
    perf = {'High Performance': 0, 'Medium Performance': 0, 'Low Performance': 0}
    for pred in latest_preds.values():
        level = pred.level if hasattr(pred, 'level') else pred
        if level in perf:
            perf[level] += 1
    return perf


def _weighted_avg_from_agg(agg: dict) -> float:
    """DB aggregation natijasidan weighted o'rtacha ball hisoblash"""
    if agg.get('avg_att') is None:
        return 0.0
    return round(
        (agg['avg_att']  or 0) * 0.2 +
        (agg['avg_hw']   or 0) * 0.2 +
        (agg['avg_quiz'] or 0) * 0.3 +
        (agg['avg_exam'] or 0) * 0.3,
        1
    )


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
                'average_score':            openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    description='Weighted formula: att×0.2 + hw×0.2 + quiz×0.3 + exam×0.3'
                ),
                'performance_distribution': openapi.Schema(type=openapi.TYPE_OBJECT),
            }
        )}
    )
    def get(self, request):
        teacher = request.user

        total_courses  = Course.objects.filter(teacher=teacher).count()
        total_groups   = Group.objects.filter(course__teacher=teacher).count()
        total_students = Student.objects.filter(group__course__teacher=teacher).count()

        # ✅ Weighted formula: exam only emas, barcha 4 ko'rsatkich
        agg = Score.objects.filter(
            student__group__course__teacher=teacher
        ).aggregate(
            avg_att=Avg('attendance'),
            avg_hw=Avg('homework'),
            avg_quiz=Avg('quiz'),
            avg_exam=Avg('exam'),
        )
        average_score = _weighted_avg_from_agg(agg)

        student_ids  = Student.objects.filter(
            group__course__teacher=teacher
        ).values_list('id', flat=True)

        latest_preds = _latest_predictions_by_student(student_ids)
        perf         = _performance_distribution(latest_preds)

        return Response({
            'total_courses':            total_courses,
            'total_groups':             total_groups,
            'total_students':           total_students,
            'at_risk_students':         perf.get('Low Performance', 0),
            'average_score':            average_score,
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
            openapi.Parameter('course_id', openapi.IN_PATH, type=openapi.TYPE_INTEGER)
        ]
    )
    def get(self, request, course_id):
        try:
            course = Course.objects.get(id=course_id, teacher=request.user)
        except Course.DoesNotExist:
            return Response({'error': {'code': 404, 'message': 'Kurs topilmadi'}}, status=404)

        groups = Group.objects.filter(course=course).annotate(s_count=Count('students'))
        groups_data = []
        for group in groups:
            agg = Score.objects.filter(student__group=group).aggregate(
                avg_attendance=Avg('attendance'),
                avg_homework=Avg('homework'),
                avg_quiz=Avg('quiz'),
                avg_exam=Avg('exam'),
            )
            groups_data.append({
                'group_id':       group.id,
                'group_name':     group.name,
                'student_count':  group.s_count,
                'avg_attendance': round(agg['avg_attendance'] or 0, 1),
                'avg_homework':   round(agg['avg_homework']   or 0, 1),
                'avg_quiz':       round(agg['avg_quiz']       or 0, 1),
                'avg_exam':       round(agg['avg_exam']       or 0, 1),
                'avg_weighted':   _weighted_avg_from_agg({
                    'avg_att':  agg['avg_attendance'],
                    'avg_hw':   agg['avg_homework'],
                    'avg_quiz': agg['avg_quiz'],
                    'avg_exam': agg['avg_exam'],
                }),
            })

        student_ids  = Student.objects.filter(group__course=course).values_list('id', flat=True)
        latest_preds = _latest_predictions_by_student(student_ids)
        perf         = _performance_distribution(latest_preds)

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
        student_ids = Student.objects.filter(
            group__course__teacher=request.user
        ).values_list('id', flat=True)

        latest_preds = _latest_predictions_by_student(student_ids)

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
            for p in Prediction.objects.filter(
                student_id__in=student_ids
            ).select_related(
                'student', 'student__group', 'student__group__course'
            ).order_by('student_id', '-predicted_at')
            if p.student_id in latest_preds
            and latest_preds[p.student_id].id == p.id
            and p.level == 'Low Performance'
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
            return Response({'error': {'code': 404, 'message': 'Guruh topilmadi'}}, status=404)

        students     = Student.objects.filter(group=group).select_related('score')
        student_ids  = [s.id for s in students]
        latest_preds = _latest_predictions_by_student(student_ids)

        student_data = []
        for student in students:
            try:
                s   = student.score
                avg = round(
                    s.attendance * 0.2 + s.homework * 0.2 +
                    s.quiz * 0.3 + s.exam * 0.3, 1
                )
                scores_dict = {
                    'attendance': s.attendance,
                    'homework':   s.homework,
                    'quiz':       s.quiz,
                    'exam':       s.exam,
                }
            except Exception:
                avg         = 0.0
                scores_dict = {'attendance': 0, 'homework': 0, 'quiz': 0, 'exam': 0}

            pred = latest_preds.get(student.id)
            student_data.append({
                'student_id':      student.id,
                'student_name':    student.name,
                'avg_score':       avg,
                'scores':          scores_dict,
                'level':           pred.level           if pred else None,
                'predicted_score': pred.predicted_score if pred else None,
                'risk_percentage': pred.risk_percentage if pred else None,
            })

        return Response({
            'group_id':       group.id,
            'group_name':     group.name,
            'course_name':    group.course.name,
            'total_students': len(student_data),
            'students':       student_data,
        })
