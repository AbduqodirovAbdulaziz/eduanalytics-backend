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
        db_table = 'courses'
        verbose_name = 'Kurs'
        verbose_name_plural = 'Kurslar'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['teacher', '-created_at']),
        ]

    def __str__(self):
        return self.name

    def group_count(self):
        """Guruhlar sonini olish (prefetch_related bilan optimizatsiya)"""
        return self.groups.count()

    def student_count(self):
        """O'quvchilar sonini olish (prefetch_related bilan optimizatsiya)"""
        from apps.students.models import Student
        return Student.objects.filter(group__course=self).count()

    def average_score(self):
        """O'rtacha ball (select_related bilan optimizatsiya)"""
        from apps.students.models import Score
        result = Score.objects.filter(
            student__group__course=self
        ).aggregate(avg=Avg('exam'))
        val = result.get('avg')
        return round(val, 1) if val else 0.0
