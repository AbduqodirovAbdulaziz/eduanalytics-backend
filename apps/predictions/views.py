from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

from apps.students.models import Student
from .models import Prediction
from .serializers import PredictRequestSerializer, BatchPredictRequestSerializer, PredictionSerializer
from ml.ml_service import get_prediction

logger = logging.getLogger(__name__)

predict_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['student_id', 'attendance', 'homework', 'quiz', 'exam'],
    properties={
        'student_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=3),
        'attendance': openapi.Schema(type=openapi.TYPE_NUMBER, example=45.0, description='0-100'),
        'homework':   openapi.Schema(type=openapi.TYPE_NUMBER, example=38.0, description='0-100'),
        'quiz':       openapi.Schema(type=openapi.TYPE_NUMBER, example=42.0, description='0-100'),
        'exam':       openapi.Schema(type=openapi.TYPE_NUMBER, example=35.0, description='0-100'),
    }
)

predict_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'student_id':      openapi.Schema(type=openapi.TYPE_INTEGER),
        'student_name':    openapi.Schema(type=openapi.TYPE_STRING),
        'level':           openapi.Schema(type=openapi.TYPE_STRING,
                            enum=['High Performance', 'Medium Performance', 'Low Performance']),
        'risk_percentage': openapi.Schema(type=openapi.TYPE_NUMBER),
        'predicted_score': openapi.Schema(type=openapi.TYPE_NUMBER),
        'recommendation':  openapi.Schema(type=openapi.TYPE_STRING),
        'predicted_at':    openapi.Schema(type=openapi.TYPE_STRING),
    }
)


class PredictView(APIView):
    """Bitta o'quvchi uchun ML prognoz"""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_id='predict_single',
        operation_summary='Bitta o\'quvchi prognozi',
        operation_description=(
            'O\'quvchining 4 ko\'rsatkichi asosida ML prognoz qaytaradi.\n\n'
            '**Natija darajalari:**\n'
            '- `High Performance` — predicted_score ≥ 70\n'
            '- `Medium Performance` — 40 ≤ predicted_score < 70\n'
            '- `Low Performance` — predicted_score < 40'
        ),
        tags=['🤖 ML Prognoz'],
        request_body=predict_request_schema,
        responses={200: predict_response_schema, 422: 'Validatsiya xatosi'}
    )
    def post(self, request):
        serializer = PredictRequestSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(
                {'error': {'code': 422, 'message': serializer.errors}},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        data = dict(serializer.validated_data)
        try:
            student = Student.objects.select_related('group', 'group__course').get(
                id=data.pop('student_id')
            )
            # Barcha qiymatlarni float ga convert qilish
            att  = float(data.get('attendance', 0) or 0)
            hw   = float(data.get('homework',   0) or 0)
            quiz = float(data.get('quiz',       0) or 0)
            exam = float(data.get('exam',       0) or 0)

            result = get_prediction(att, hw, quiz, exam)

            prediction, _ = Prediction.objects.update_or_create(
                student=student,
                defaults={
                    'attendance':      att,
                    'homework':        hw,
                    'quiz':            quiz,
                    'exam':            exam,
                    'predicted_score': result['predicted_score'],
                    'level':           result['level'],
                    'risk_percentage': result['risk_percentage'],
                    'recommendation':  result['recommendation'],
                },
            )
            return Response({
                'student_id':      student.id,
                'student_name':    student.name,
                'level':           result['level'],
                'risk_percentage': result['risk_percentage'],
                'predicted_score': result['predicted_score'],
                'recommendation':  result['recommendation'],
                'predicted_at':    prediction.predicted_at,
            })
        except Student.DoesNotExist:
            return Response(
                {'error': {'code': 404, 'message': "O'quvchi topilmadi"}},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"PredictView error: {e}", exc_info=True)
            return Response(
                {'error': {'code': 500, 'message': f"Prognoz xatosi: {str(e)}"}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BatchPredictView(APIView):
    """Ko'p o'quvchilar uchun batch prognoz"""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_id='predict_batch',
        operation_summary='Batch prognoz (ko\'p o\'quvchi)',
        tags=['🤖 ML Prognoz'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['student_ids'],
            properties={
                'student_ids': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                    example=[1, 2, 3, 4, 5]
                )
            }
        ),
        responses={200: 'Barcha o\'quvchilar natijalari ro\'yxati'}
    )
    def post(self, request):
        serializer = BatchPredictRequestSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(
                {'error': {'code': 422, 'message': serializer.errors}},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        student_ids = serializer.validated_data['student_ids']
        students = Student.objects.filter(id__in=student_ids).select_related('score')
        results = []
        for student in students:
            try:
                try:
                    s = student.score
                    att  = float(s.attendance or 0)
                    hw   = float(s.homework   or 0)
                    quiz = float(s.quiz       or 0)
                    exam = float(s.exam       or 0)
                except Exception:
                    att = hw = quiz = exam = 0.0

                result = get_prediction(att, hw, quiz, exam)
                pred, _ = Prediction.objects.update_or_create(
                    student=student,
                    defaults={
                        'attendance': att, 'homework': hw,
                        'quiz': quiz, 'exam': exam, **result,
                    }
                )
                results.append({
                    'student_id':   student.id,
                    'student_name': student.name,
                    **result,
                    'predicted_at': pred.predicted_at,
                })
            except Exception as e:
                logger.error(f"Batch predict error for student {student.id}: {e}")
                results.append({
                    'student_id':   student.id,
                    'student_name': student.name,
                    'error':        str(e),
                })
        return Response({'data': results, 'total': len(results)})


class PredictionHistoryView(APIView):
    """O'quvchi prognoz tarixi"""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_id='predict_history',
        operation_summary='Prognoz tarixi',
        tags=['🤖 ML Prognoz'],
        manual_parameters=[
            openapi.Parameter('student_id', openapi.IN_PATH, type=openapi.TYPE_INTEGER,
                              description='O\'quvchi ID si')
        ],
        responses={200: PredictionSerializer(many=True)}
    )
    def get(self, request, student_id):
        student = Student.objects.filter(id=student_id, group__course__teacher=request.user).first()
        if not student:
            return Response({'error': {'code': 404, 'message': "O'quvchi topilmadi"}}, status=404)
        predictions = Prediction.objects.filter(student=student)[:10]
        return Response({'data': PredictionSerializer(predictions, many=True).data})
