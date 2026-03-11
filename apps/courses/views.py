from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Course
from .serializers import CourseSerializer, CourseCreateSerializer


class CourseListCreateView(generics.ListCreateAPIView):
    """Kurslar ro'yxati va yaratish"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Course.objects.filter(teacher=self.request.user)

    def get_serializer_class(self):
        return CourseCreateSerializer if self.request.method == 'POST' else CourseSerializer

    @swagger_auto_schema(
        operation_id='courses_list',
        operation_summary='Barcha kurslar',
        tags=['📚 Kurslar'],
        responses={200: CourseSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        serializer = CourseSerializer(self.get_queryset(), many=True)
        return Response({'data': serializer.data})

    @swagger_auto_schema(
        operation_id='courses_create',
        operation_summary='Yangi kurs yaratish',
        tags=['📚 Kurslar'],
        request_body=CourseCreateSerializer,
        responses={201: CourseSerializer}
    )
    def create(self, request, *args, **kwargs):
        serializer = CourseCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            course = serializer.save()
            return Response(CourseSerializer(course).data, status=status.HTTP_201_CREATED)
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class CourseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Kurs tafsiloti, yangilash, o'chirish"""
    permission_classes = [IsAuthenticated]
    serializer_class = CourseSerializer

    def get_queryset(self):
        return Course.objects.filter(teacher=self.request.user)

    @swagger_auto_schema(operation_id='courses_get',    operation_summary='Kurs tafsiloti',  tags=['📚 Kurslar'])
    def retrieve(self, request, *args, **kwargs): return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(operation_id='courses_update', operation_summary='Kursni yangilash', tags=['📚 Kurslar'])
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        s = CourseCreateSerializer(instance, data=request.data, partial=True, context={'request': request})
        if s.is_valid():
            return Response(CourseSerializer(s.save()).data)
        return Response({'error': s.errors}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(operation_id='courses_delete', operation_summary='Kursni o\'chirish', tags=['📚 Kurslar'])
    def destroy(self, request, *args, **kwargs): return super().destroy(request, *args, **kwargs)
