from django.db import models
from django.db.models import Avg
from apps.authentication.models import Teacher


class Course(models.Model):
    """Kurs modeli"""
    SUBJECT_CHOICES = [
        ('math',       'Matematika'),
        ('physics',    'Fizika'),
        ('chemistry',  'Kimyo'),
        ('biology',    'Biologiya'),
        ('history',    'Tarix'),
        ('geography',  'Geografiya'),
        ('literature', 'Adabiyot'),
        ('english',    'Ingliz tili'),
        ('uzbek',      "O'zbek tili"),
        ('it',         'Informatika'),
        ('other',      'Boshqa'),
    ]

    teacher     = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='courses')
    name        = models.CharField(max_length=200, verbose_name="Kurs nomi")
    subject     = models.CharField(max_length=50, choices=SUBJECT_CHOICES, default='other')
    description = models.TextField(blank=True, null=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table            = 'courses'
        verbose_name        = 'Kurs'
        verbose_name_plural = 'Kurslar'
        ordering            = ['-created_at']
        indexes             = [
            models.Index(fields=['teacher', '-created_at']),
        ]

    def __str__(self):
        return self.name

    def group_count(self) -> int:
        return self.groups.count()

    def student_count(self) -> int:
        from apps.students.models import Student
        return Student.objects.filter(group__course=self).count()

    def average_score(self) -> float:
        """
        Weighted formula asosida o'rtacha ball:
        att×0.2 + hw×0.2 + quiz×0.3 + exam×0.3
        (faqat exam emas — barcha ko'rsatkichlar hisobga olinadi)
        """
        from apps.students.models import Score
        agg = Score.objects.filter(
            student__group__course=self
        ).aggregate(
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
