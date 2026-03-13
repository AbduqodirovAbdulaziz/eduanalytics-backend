from rest_framework import serializers
from .models import Student, Score


class ScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Score
        fields = ['attendance', 'homework', 'quiz', 'exam']


class StudentSerializer(serializers.ModelSerializer):
    scores      = ScoreSerializer(source='score', read_only=True)
    group_name  = serializers.CharField(source='group.name', read_only=True)
    course_id   = serializers.IntegerField(source='group.course.id', read_only=True)
    course_name = serializers.CharField(source='group.course.name', read_only=True)

    class Meta:
        model = Student
        fields = [
            'id', 'name', 'email', 'phone',
            'group', 'group_name', 'course_id', 'course_name',
            'scores', 'enrolled_at'
        ]
        read_only_fields = ['id', 'enrolled_at']


class StudentListSerializer(serializers.ModelSerializer):
    """Ro'yxat uchun serializer — Flutter StudentModel bilan to'liq mos"""
    group_name  = serializers.CharField(source='group.name', read_only=True)
    course_id   = serializers.IntegerField(source='group.course.id', read_only=True)
    course_name = serializers.CharField(source='group.course.name', read_only=True)
    scores      = ScoreSerializer(source='score', read_only=True)
    avg_score   = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            'id', 'name', 'email',
            'group', 'group_name',
            'course_id', 'course_name',
            'scores', 'avg_score', 'enrolled_at'
        ]

    def get_avg_score(self, obj):
        try:
            s = obj.score
            avg = (s.attendance * 0.2 + s.homework * 0.2 +
                   s.quiz * 0.3 + s.exam * 0.3)
            return round(avg, 1)
        except Score.DoesNotExist:
            return None


class StudentCreateSerializer(serializers.ModelSerializer):
    attendance = serializers.FloatField(default=0.0, min_value=0, max_value=100, write_only=True)
    homework   = serializers.FloatField(default=0.0, min_value=0, max_value=100, write_only=True)
    quiz       = serializers.FloatField(default=0.0, min_value=0, max_value=100, write_only=True)
    exam       = serializers.FloatField(default=0.0, min_value=0, max_value=100, write_only=True)

    class Meta:
        model = Student
        fields = ['name', 'email', 'phone', 'group', 'attendance', 'homework', 'quiz', 'exam']

    def validate_group(self, group):
        teacher = self.context['request'].user
        if group.course.teacher != teacher:
            raise serializers.ValidationError("Bu guruh sizga tegishli emas!")
        return group

    def create(self, validated_data):
        scores_data = {
            'attendance': validated_data.pop('attendance', 0),
            'homework':   validated_data.pop('homework', 0),
            'quiz':       validated_data.pop('quiz', 0),
            'exam':       validated_data.pop('exam', 0),
        }
        student = Student.objects.create(**validated_data)
        Score.objects.create(student=student, **scores_data)
        return student

    def update(self, instance, validated_data):
        scores_data = {
            'attendance': validated_data.pop('attendance', None),
            'homework':   validated_data.pop('homework', None),
            'quiz':       validated_data.pop('quiz', None),
            'exam':       validated_data.pop('exam', None),
        }
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Score yangilash
        score, _ = Score.objects.get_or_create(student=instance)
        for field, value in scores_data.items():
            if value is not None:
                setattr(score, field, value)
        score.save()
        return instance
