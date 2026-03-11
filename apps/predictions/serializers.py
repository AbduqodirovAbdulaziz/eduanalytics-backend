from rest_framework import serializers
from apps.students.models import Student
from .models import Prediction


class PredictRequestSerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    attendance = serializers.FloatField(min_value=0, max_value=100)
    homework   = serializers.FloatField(min_value=0, max_value=100)
    quiz       = serializers.FloatField(min_value=0, max_value=100)
    exam       = serializers.FloatField(min_value=0, max_value=100)

    def validate_student_id(self, value):
        teacher = self.context['request'].user
        try:
            student = Student.objects.get(id=value, group__course__teacher=teacher)
        except Student.DoesNotExist:
            raise serializers.ValidationError("O'quvchi topilmadi yoki sizga tegishli emas!")
        return value


class BatchPredictRequestSerializer(serializers.Serializer):
    student_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=100
    )

    def validate_student_ids(self, ids):
        teacher = self.context['request'].user
        existing = Student.objects.filter(
            id__in=ids, group__course__teacher=teacher
        ).values_list('id', flat=True)
        missing = set(ids) - set(existing)
        if missing:
            raise serializers.ValidationError(
                f"Bu ID lar topilmadi yoki sizga tegishli emas: {list(missing)}"
            )
        return ids


class PredictionSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)

    class Meta:
        model = Prediction
        fields = [
            'student_id', 'student_name',
            'predicted_score', 'level', 'risk_percentage',
            'recommendation', 'predicted_at'
        ]
