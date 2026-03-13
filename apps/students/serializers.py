"""
EduAnalytics — Students App Serializers
Barcha serialiaztor sinflari: Student, Score, DailyAttendance, HomeworkSubmission, QuizResult
"""
from rest_framework import serializers
from django.utils import timezone
from .models import Student, Score, DailyAttendance, HomeworkSubmission, QuizResult


# ═══════════════════════════════════════════════════════════════
#  YORDAMCHI MIXIN — Teacher permission tekshiruvi
# ═══════════════════════════════════════════════════════════════

class TeacherOwnsMixin:
    """O'quvchi joriy o'qituvchiga tegishli ekanligini tekshirish"""
    def validate_student(self, student):
        teacher = self.context['request'].user
        if student.group.course.teacher != teacher:
            raise serializers.ValidationError("Bu o'quvchi sizga tegishli emas!")
        return student


# ═══════════════════════════════════════════════════════════════
#  SCORE SERIALIZER
# ═══════════════════════════════════════════════════════════════

class ScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Score
        fields = ['attendance', 'homework', 'quiz', 'exam', 'updated_at']
        read_only_fields = ['updated_at']


# ═══════════════════════════════════════════════════════════════
#  STUDENT SERIALIZERS
# ═══════════════════════════════════════════════════════════════

class StudentSerializer(serializers.ModelSerializer):
    """Batafsil — bitta o'quvchi uchun"""
    scores      = ScoreSerializer(source='score', read_only=True)
    group_name  = serializers.CharField(source='group.name', read_only=True)
    course_id   = serializers.IntegerField(source='group.course.id', read_only=True)
    course_name = serializers.CharField(source='group.course.name', read_only=True)
    avg_score   = serializers.SerializerMethodField()

    class Meta:
        model  = Student
        fields = [
            'id', 'name', 'email', 'phone',
            'group', 'group_name', 'course_id', 'course_name',
            'scores', 'avg_score', 'enrolled_at',
        ]
        read_only_fields = ['id', 'enrolled_at']

    def get_avg_score(self, obj):
        try:
            s = obj.score
            return round(
                s.attendance * 0.2 + s.homework * 0.2 +
                s.quiz * 0.3 + s.exam * 0.3, 1
            )
        except Score.DoesNotExist:
            return None


class StudentListSerializer(serializers.ModelSerializer):
    """Ro'yxat uchun — yengil versiya"""
    group_name  = serializers.CharField(source='group.name', read_only=True)
    course_id   = serializers.IntegerField(source='group.course.id', read_only=True)
    course_name = serializers.CharField(source='group.course.name', read_only=True)
    scores      = ScoreSerializer(source='score', read_only=True)
    avg_score   = serializers.SerializerMethodField()

    class Meta:
        model  = Student
        fields = [
            'id', 'name', 'email',
            'group', 'group_name',
            'course_id', 'course_name',
            'scores', 'avg_score', 'enrolled_at',
        ]

    def get_avg_score(self, obj):
        try:
            s = obj.score
            return round(
                s.attendance * 0.2 + s.homework * 0.2 +
                s.quiz * 0.3 + s.exam * 0.3, 1
            )
        except Score.DoesNotExist:
            return None


class StudentCreateSerializer(serializers.ModelSerializer):
    """
    O'quvchi yaratish / yangilash.
    attendance/homework/quiz/exam — boshlang'ich qiymatlar uchun (ixtiyoriy).
    Kunlik yozuvlar keyin qo'shilganda Score avtomatik yangilanadi.
    """
    attendance = serializers.FloatField(default=0.0, min_value=0, max_value=100, write_only=True)
    homework   = serializers.FloatField(default=0.0, min_value=0, max_value=100, write_only=True)
    quiz       = serializers.FloatField(default=0.0, min_value=0, max_value=100, write_only=True)
    exam       = serializers.FloatField(default=0.0, min_value=0, max_value=100, write_only=True)

    class Meta:
        model  = Student
        fields = ['name', 'email', 'phone', 'group', 'attendance', 'homework', 'quiz', 'exam']

    def validate_group(self, group):
        teacher = self.context['request'].user
        if group.course.teacher != teacher:
            raise serializers.ValidationError("Bu guruh sizga tegishli emas!")
        return group

    def create(self, validated_data):
        scores_data = {
            'attendance': validated_data.pop('attendance', 0.0),
            'homework':   validated_data.pop('homework',   0.0),
            'quiz':       validated_data.pop('quiz',       0.0),
            'exam':       validated_data.pop('exam',       0.0),
        }
        student = Student.objects.create(**validated_data)
        # Signal allaqachon default(0,0,0,0) Score yaratdi — faqat update:
        Score.objects.filter(student=student).update(**scores_data)
        return student

    def update(self, instance, validated_data):
        scores_data = {
            'attendance': validated_data.pop('attendance', None),
            'homework':   validated_data.pop('homework',   None),
            'quiz':       validated_data.pop('quiz',       None),
            'exam':       validated_data.pop('exam',       None),
        }
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        score, _ = Score.objects.get_or_create(student=instance)
        for field, value in scores_data.items():
            if value is not None:
                setattr(score, field, value)
        score.save()
        return instance


# ═══════════════════════════════════════════════════════════════
#  DAVOMAT SERIALIZERS
# ═══════════════════════════════════════════════════════════════

class DailyAttendanceSerializer(serializers.ModelSerializer):
    """O'qish uchun"""
    student_name = serializers.CharField(source='student.name', read_only=True)

    class Meta:
        model  = DailyAttendance
        fields = [
            'id', 'student', 'student_name', 'date',
            'lesson_number', 'is_present', 'is_excused', 'note', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class DailyAttendanceCreateSerializer(TeacherOwnsMixin, serializers.ModelSerializer):
    """Bitta davomat yozuvi yaratish"""
    class Meta:
        model  = DailyAttendance
        fields = ['student', 'date', 'lesson_number', 'is_present', 'is_excused', 'note']

    def validate_date(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("Kelajak sanasi kiritib bo'lmaydi!")
        return value


class BulkAttendanceItemSerializer(serializers.Serializer):
    """Guruh davomat kiritishda har bir o'quvchi uchun"""
    student_id = serializers.IntegerField()
    is_present = serializers.BooleanField(default=True)
    is_excused = serializers.BooleanField(default=False)
    note       = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')


class BulkAttendanceSerializer(serializers.Serializer):
    """
    Bir guruh uchun bir kunda bir vaqtda davomat kiritish.
    POST /api/v1/attendance/bulk/
    """
    group_id      = serializers.IntegerField()
    date          = serializers.DateField()
    lesson_number = serializers.IntegerField(default=1, min_value=1, max_value=20)
    attendances   = BulkAttendanceItemSerializer(many=True, min_length=1)

    def validate_date(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("Kelajak sanasi kiritib bo'lmaydi!")
        return value

    def validate(self, data):
        from apps.groups.models import Group
        teacher = self.context['request'].user
        try:
            group = Group.objects.get(id=data['group_id'], course__teacher=teacher)
        except Group.DoesNotExist:
            raise serializers.ValidationError({"group_id": "Guruh topilmadi yoki sizga tegishli emas!"})

        student_ids_in_group = set(group.students.values_list('id', flat=True))
        submitted_ids        = {item['student_id'] for item in data['attendances']}
        invalid_ids          = submitted_ids - student_ids_in_group
        if invalid_ids:
            raise serializers.ValidationError(
                {"attendances": f"Bu o'quvchilar guruhga tegishli emas: {list(invalid_ids)}"}
            )

        data['_group'] = group
        return data


# ═══════════════════════════════════════════════════════════════
#  UY VAZIFASI SERIALIZERS
# ═══════════════════════════════════════════════════════════════

class HomeworkSubmissionSerializer(serializers.ModelSerializer):
    """O'qish uchun"""
    student_name = serializers.CharField(source='student.name', read_only=True)
    percentage   = serializers.ReadOnlyField()

    class Meta:
        model  = HomeworkSubmission
        fields = [
            'id', 'student', 'student_name', 'date', 'title',
            'max_score', 'score', 'submitted', 'note', 'percentage', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class HomeworkSubmissionCreateSerializer(TeacherOwnsMixin, serializers.ModelSerializer):
    """Uy vazifasi kiritish"""
    class Meta:
        model  = HomeworkSubmission
        fields = ['student', 'date', 'title', 'max_score', 'score', 'submitted', 'note']

    def validate(self, data):
        if data.get('score', 0) > data.get('max_score', 10.0):
            raise serializers.ValidationError(
                {"score": f"Ball ({data['score']}) maksimal balldan ({data['max_score']}) oshib ketdi!"}
            )
        return data

    def validate_date(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("Kelajak sanasi kiritib bo'lmaydi!")
        return value


class BulkHomeworkSerializer(serializers.Serializer):
    """
    Bir guruh uchun bir uy vazifasini bir vaqtda kiritish.
    POST /api/v1/homework/bulk/
    """
    class HomeworkItemSerializer(serializers.Serializer):
        student_id = serializers.IntegerField()
        score      = serializers.FloatField(min_value=0)
        submitted  = serializers.BooleanField(default=True)
        note       = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')

    group_id  = serializers.IntegerField()
    date      = serializers.DateField()
    title     = serializers.CharField(max_length=200)
    max_score = serializers.FloatField(default=10.0, min_value=0.1)
    students  = HomeworkItemSerializer(many=True, min_length=1)

    def validate_date(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("Kelajak sanasi kiritib bo'lmaydi!")
        return value

    def validate(self, data):
        from apps.groups.models import Group
        teacher = self.context['request'].user
        try:
            group = Group.objects.get(id=data['group_id'], course__teacher=teacher)
        except Group.DoesNotExist:
            raise serializers.ValidationError({"group_id": "Guruh topilmadi yoki sizga tegishli emas!"})
        data['_group'] = group
        return data


# ═══════════════════════════════════════════════════════════════
#  QUIZ / IMTIHON SERIALIZERS
# ═══════════════════════════════════════════════════════════════

class QuizResultSerializer(serializers.ModelSerializer):
    """O'qish uchun"""
    student_name      = serializers.CharField(source='student.name', read_only=True)
    percentage        = serializers.ReadOnlyField()
    quiz_type_display = serializers.CharField(source='get_quiz_type_display', read_only=True)

    class Meta:
        model  = QuizResult
        fields = [
            'id', 'student', 'student_name', 'date',
            'quiz_type', 'quiz_type_display', 'topic',
            'max_score', 'score', 'note', 'percentage', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class QuizResultCreateSerializer(TeacherOwnsMixin, serializers.ModelSerializer):
    """Quiz / imtihon natijasi kiritish"""
    class Meta:
        model  = QuizResult
        fields = ['student', 'date', 'quiz_type', 'topic', 'max_score', 'score', 'note']

    def validate(self, data):
        if data.get('score', 0) > data.get('max_score', 100.0):
            raise serializers.ValidationError(
                {"score": f"Ball ({data['score']}) maksimal balldan ({data['max_score']}) oshib ketdi!"}
            )
        return data

    def validate_date(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("Kelajak sanasi kiritib bo'lmaydi!")
        return value


class BulkQuizSerializer(serializers.Serializer):
    """
    Bir guruh uchun bir quiz/imtihonni bir vaqtda kiritish.
    POST /api/v1/quiz/bulk/
    """
    class QuizItemSerializer(serializers.Serializer):
        student_id = serializers.IntegerField()
        score      = serializers.FloatField(min_value=0)
        note       = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')

    group_id  = serializers.IntegerField()
    date      = serializers.DateField()
    quiz_type = serializers.ChoiceField(choices=['quiz', 'classwork', 'exam'])
    topic     = serializers.CharField(max_length=200)
    max_score = serializers.FloatField(default=100.0, min_value=0.1)
    students  = QuizItemSerializer(many=True, min_length=1)

    def validate_date(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("Kelajak sanasi kiritib bo'lmaydi!")
        return value

    def validate(self, data):
        from apps.groups.models import Group
        teacher = self.context['request'].user
        try:
            group = Group.objects.get(id=data['group_id'], course__teacher=teacher)
        except Group.DoesNotExist:
            raise serializers.ValidationError({"group_id": "Guruh topilmadi yoki sizga tegishli emas!"})
        data['_group'] = group
        return data


# ═══════════════════════════════════════════════════════════════
#  PROGRESS SERIALIZER
# ═══════════════════════════════════════════════════════════════

class StudentProgressSerializer(serializers.Serializer):
    """
    O'quvchi progress ma'lumotlari (frontend uchun grafik data).
    GET /api/v1/students/<id>/progress/
    """
    student_id   = serializers.IntegerField()
    student_name = serializers.CharField()
    current_score = serializers.DictField()
    attendance_history = serializers.ListField()
    homework_history   = serializers.ListField()
    quiz_history       = serializers.ListField()
    exam_history       = serializers.ListField()
    trends             = serializers.DictField()
    summary            = serializers.DictField()
