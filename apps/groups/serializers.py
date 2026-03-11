from rest_framework import serializers
from .models import Group


class GroupSerializer(serializers.ModelSerializer):
    course_name   = serializers.CharField(source='course.name', read_only=True)
    student_count = serializers.ReadOnlyField()

    class Meta:
        model = Group
        fields = ['id', 'name', 'course', 'course_name', 'student_count', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']


class GroupCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['name', 'course', 'description']

    def validate_course(self, course):
        teacher = self.context['request'].user
        if course.teacher != teacher:
            raise serializers.ValidationError("Bu kurs sizga tegishli emas!")
        return course
