from django.db import models
from apps.students.models import Student


class Prediction(models.Model):
    """ML prognoz natijalari"""
    LEVEL_CHOICES = [
        ('High Performance',   'Yuqori daraja'),
        ('Medium Performance', "O'rta daraja"),
        ('Low Performance',    'Past daraja'),
    ]

    student         = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name='predictions'
    )
    attendance      = models.FloatField()
    homework        = models.FloatField()
    quiz            = models.FloatField()
    exam            = models.FloatField()
    predicted_score = models.FloatField()
    level           = models.CharField(max_length=30, choices=LEVEL_CHOICES)
    risk_percentage = models.FloatField()
    recommendation  = models.TextField()
    predicted_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'predictions'
        verbose_name = 'Prognoz'
        verbose_name_plural = 'Prognozlar'
        ordering = ['-predicted_at']

    def __str__(self):
        return f"{self.student.name} — {self.level}"
