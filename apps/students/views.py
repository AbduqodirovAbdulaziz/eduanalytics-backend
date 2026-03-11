from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import Student
from .serializers import StudentSerializer, StudentListSerializer, StudentCreateSerializer


class StudentListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/students?page=1&limit=20&group_id=1&course_id=2
    POST /api/v1/students
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        qs = Student.objects.filter(
            group__course__teacher=self.request.user
        ).select_related('group', 'group__course').prefetch_related('score')

        group_id = self.request.query_params.get('group_id')
        course_id = self.request.query_params.get('course_id')

        if group_id:
            qs = qs.filter(group_id=group_id)
        if course_id:
            qs = qs.filter(group__course_id=course_id)
        return qs

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return StudentCreateSerializer
        return StudentListSerializer

    def create(self, request, *args, **kwargs):
        serializer = StudentCreateSerializer(
            data=request.data, context={'request': request}
        )
        if serializer.is_valid():
            student = serializer.save()
            return Response(
                StudentSerializer(student).data,
                status=status.HTTP_201_CREATED
            )
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class StudentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/DELETE /api/v1/students/:id"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Student.objects.filter(
            group__course__teacher=self.request.user
        ).select_related('group', 'group__course').prefetch_related('score')

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return StudentCreateSerializer
        return StudentSerializer

    def retrieve(self, request, *args, **kwargs):
        student = self.get_object()
        return Response(StudentSerializer(student).data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        student = self.get_object()
        serializer = StudentCreateSerializer(
            student, data=request.data, partial=partial,
            context={'request': request}
        )
        if serializer.is_valid():
            student = serializer.save()
            return Response(StudentSerializer(student).data)
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
