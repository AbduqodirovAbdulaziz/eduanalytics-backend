from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.students.models import Student
from .models import Prediction
from .serializers import PredictRequestSerializer, BatchPredictRequestSerializer, PredictionSerializer
from ml.ml_service import get_prediction


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
        student = Student.objects.get(id=data.pop('student_id'))
        result = get_prediction(data['attendance'], data['homework'], data['quiz'], data['exam'])
        prediction, _ = Prediction.objects.update_or_create(
            student=student,
            defaults={**data, **result},
        )
        return Response({
            'student_id': student.id, 'student_name': student.name,
            'level': result['level'], 'risk_percentage': result['risk_percentage'],
            'predicted_score': result['predicted_score'],
            'recommendation': result['recommendation'],
            'predicted_at': prediction.predicted_at,
        })


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
                s = student.score
                result = get_prediction(s.attendance, s.homework, s.quiz, s.exam)
                pred, _ = Prediction.objects.update_or_create(
                    student=student,
                    defaults={
                        'attendance': s.attendance,
                        'homework': s.homework,
                        'quiz': s.quiz,
                        'exam': s.exam,
                        **result,
                    }
                )
                results.append({
                    'student_id': student.id, 'student_name': student.name,
                    **result, 'predicted_at': pred.predicted_at,
                })
            except Exception as e:
                results.append({'student_id': student.id, 'student_name': student.name, 'error': str(e)})
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
