from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Group
from .serializers import GroupSerializer, GroupCreateSerializer


class GroupListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/v1/groups"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Group.objects.filter(course__teacher=self.request.user)
        course_id = self.request.query_params.get('course_id')
        if course_id:
            qs = qs.filter(course_id=course_id)
        return qs

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = GroupSerializer(queryset, many=True)
        return Response({'data': serializer.data})

    def create(self, request, *args, **kwargs):
        serializer = GroupCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            group = serializer.save()
            return Response(GroupSerializer(group).data, status=status.HTTP_201_CREATED)
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class GroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/DELETE /api/v1/groups/:id"""
    permission_classes = [IsAuthenticated]
    serializer_class = GroupSerializer

    def get_queryset(self):
        return Group.objects.filter(course__teacher=self.request.user)
