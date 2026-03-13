from rest_framework import serializers
from .models import Course


class CourseSerializer(serializers.ModelSerializer):
    group_count   = serializers.ReadOnlyField()
    student_count = serializers.ReadOnlyField()
    average_score = serializers.ReadOnlyField()
    teacher_id    = serializers.IntegerField(source='teacher.id', read_only=True)

    class Meta:
        model = Course
        fields = [
            'id', 'name', 'subject', 'description',
            'teacher_id',
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
