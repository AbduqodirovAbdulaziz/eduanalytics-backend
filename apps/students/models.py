from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.groups.models import Group


class Student(models.Model):
    """O'quvchi modeli"""
    group       = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='students')
    name        = models.CharField(max_length=150, verbose_name="Ism Familiya")
    email       = models.EmailField(blank=True, null=True)
    phone       = models.CharField(max_length=20, blank=True, null=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table  = 'students'
        verbose_name = "O'quvchi"
        verbose_name_plural = "O'quvchilar"
        ordering  = ['name']
        indexes   = [
            models.Index(fields=['group', 'name']),
            models.Index(fields=['-enrolled_at']),
        ]

    def __str__(self):
        return self.name


class Score(models.Model):
    """O'quvchi natijalari modeli"""
    student    = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='score')
    attendance = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        verbose_name="Davomat (%)"
    )
    homework   = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        verbose_name="Uy vazifasi (%)"
    )
    quiz       = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        verbose_name="Quiz (%)"
    )
    exam       = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        verbose_name="Imtihon (%)"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table     = 'scores'
        verbose_name = "Natija"
        verbose_name_plural = "Natijalar"

    def __str__(self):
        return f"{self.student.name} natijalari"


# ═══════════════════════════════════════════════════════════════
#  SIGNALS
# ═══════════════════════════════════════════════════════════════

@receiver(post_save, sender=Student)
def create_score_for_student(sender, instance, created, **kwargs):
    """Yangi o'quvchi qo'shilganda Score avtomatik yaratiladi"""
    if created:
        Score.objects.get_or_create(student=instance)


@receiver(post_save, sender=Score)
def create_prediction_for_score(sender, instance, created, **kwargs):
    """
    Score saqlanganda avtomatik prognoz yaratish.
    BUG FIX: to'g'ri import yo'li — ml.ml_service (apps.ml emas!)
    BUG FIX: get_prediction funksiyasi ishlatiladi (calculate_prediction emas!)
    """
    try:
        from ml.ml_service import get_prediction          # ✅ To'g'ri import
        from apps.predictions.models import Prediction

        prediction_data = get_prediction(
            attendance=instance.attendance,
            homework=instance.homework,
            quiz=instance.quiz,
            exam=instance.exam,
        )

        Prediction.objects.update_or_create(
            student=instance.student,
            defaults={
                'attendance':      instance.attendance,
                'homework':        instance.homework,
                'quiz':            instance.quiz,
                'exam':            instance.exam,
                'predicted_score': prediction_data['predicted_score'],
                'level':           prediction_data['level'],
                'risk_percentage': prediction_data['risk_percentage'],
                'recommendation':  prediction_data['recommendation'],
            }
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Prognoz yaratishda xato: {e}")
