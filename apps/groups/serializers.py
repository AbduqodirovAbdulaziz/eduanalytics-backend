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
        model  = Group
        fields = [
            'id', 'name',
            'course', 'course_id', 'course_name',
            'student_count', 'average_score', 'at_risk_count',
            'description', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_average_score(self, obj) -> float:
        """
        Weighted formula asosida guruh o'rtacha balli.
        DB aggregation — N+1 yo'q.
        """
        from apps.students.models import Score
        agg = Score.objects.filter(student__group=obj).aggregate(
            avg_att=Avg('attendance'),
            avg_hw=Avg('homework'),
            avg_quiz=Avg('quiz'),
            avg_exam=Avg('exam'),
        )
        if agg['avg_att'] is None:
            return 0.0
        return round(
            (agg['avg_att']  or 0) * 0.2 +
            (agg['avg_hw']   or 0) * 0.2 +
            (agg['avg_quiz'] or 0) * 0.3 +
            (agg['avg_exam'] or 0) * 0.3,
            1
        )

    def get_at_risk_count(self, obj) -> int:
        """
        Xavf ostidagi o'quvchilar soni — oxirgi prognozda 'Low Performance' bo'lganlar.
        Score.weighted < 40 bo'lsa xavf bor deb hisoblanadi.
        DB aggregation orqali (N+1 yo'q).
        """
        from apps.students.models import Score
        scores = Score.objects.filter(student__group=obj).values_list(
            'attendance', 'homework', 'quiz', 'exam'
        )
        return sum(
            1 for att, hw, q, e in scores
            if (att * 0.2 + hw * 0.2 + q * 0.3 + e * 0.3) < 40
        )


class GroupCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Group
        fields = ['name', 'course', 'description']

    def validate_course(self, course):
        teacher = self.context['request'].user
        if course.teacher != teacher:
            raise serializers.ValidationError("Bu kurs sizga tegishli emas!")
        return course
