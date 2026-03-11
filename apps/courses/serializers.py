from rest_framework import serializers
from .models import Course


class CourseSerializer(serializers.ModelSerializer):
    group_count   = serializers.ReadOnlyField()
    student_count = serializers.ReadOnlyField()
    average_score = serializers.ReadOnlyField()

    class Meta:
        model = Course
        fields = [
            'id', 'name', 'subject', 'description',
            'group_count', 'student_count', 'average_score',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class CourseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['name', 'subject', 'description']

    def create(self, validated_data):
        # Teacher request.user dan olinadi
        teacher = self.context['request'].user
        return Course.objects.create(teacher=teacher, **validated_data)
