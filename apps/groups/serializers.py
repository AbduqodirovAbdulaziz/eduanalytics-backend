from rest_framework import serializers
from django.db.models import Avg
from .models import Group


class GroupSerializer(serializers.ModelSerializer):
    course_name   = serializers.CharField(source='course.name', read_only=True)
    course_id     = serializers.IntegerField(source='course.id', read_only=True)
    student_count = serializers.ReadOnlyField()
    average_score = serializers.SerializerMethodField()
    at_risk_count = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            'id', 'name',
            'course', 'course_id', 'course_name',
            'student_count', 'average_score', 'at_risk_count',
            'description', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_average_score(self, obj):
        """Guruh o'rtacha balli (attendance*0.2 + homework*0.2 + quiz*0.3 + exam*0.3)"""
        from apps.students.models import Score
        scores = Score.objects.filter(student__group=obj)
        if not scores.exists():
            return 0.0
        total = 0.0
        count = 0
        for s in scores:
            total += s.attendance * 0.2 + s.homework * 0.2 + s.quiz * 0.3 + s.exam * 0.3
            count += 1
        return round(total / count, 1) if count else 0.0

    def get_at_risk_count(self, obj):
        """Xavf ostidagi o'quvchilar soni (overall < 40)"""
        from apps.students.models import Score
        scores = Score.objects.filter(student__group=obj)
        return sum(
            1 for s in scores
            if (s.attendance * 0.2 + s.homework * 0.2 + s.quiz * 0.3 + s.exam * 0.3) < 40
        )


class GroupCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['name', 'course', 'description']

    def validate_course(self, course):
        teacher = self.context['request'].user
        if course.teacher != teacher:
            raise serializers.ValidationError("Bu kurs sizga tegishli emas!")
        return course
