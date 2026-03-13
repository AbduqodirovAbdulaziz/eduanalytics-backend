"""
EduAnalytics — Students App Models
O'quvchi, Kunlik Davomat, Uy Vazifasi, Quiz/Imtihon natijalari va Score modellari.

Arxitektura:
    Student → DailyAttendance     ─┐
    Student → HomeworkSubmission  ─┼─ Signal → recalculate_score() → Score → ML Prognoz (tarix)
    Student → QuizResult          ─┘

Muhim:
    - recalculate_score() DB aggregation ishlatadi (N+1 muammo yo'q)
    - DailyAttendance: is_present=True bo'lsa is_excused har doim False
    - HomeworkSubmission: submitted=False bo'lsa score avtomatik 0 ga tushadi
    - Prediction tarixi saqlanadi (har yangilanishda create, update_or_create emas)
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.db.models import Avg, Count, Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.groups.models import Group


# ═══════════════════════════════════════════════════════════════
#  ASOSIY MODELLAR
# ═══════════════════════════════════════════════════════════════

class Student(models.Model):
    """O'quvchi modeli"""
    group       = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='students')
    name        = models.CharField(max_length=150, verbose_name="Ism Familiya")
    email       = models.EmailField(blank=True, null=True)
    phone       = models.CharField(max_length=20, blank=True, null=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table            = 'students'
        verbose_name        = "O'quvchi"
        verbose_name_plural = "O'quvchilar"
        ordering            = ['name']
        indexes             = [
            models.Index(fields=['group', 'name']),
            models.Index(fields=['-enrolled_at']),
        ]

    def __str__(self):
        return self.name

    def get_weighted_score(self) -> float:
        """Weighted formula asosida umumiy ball (Score dan)"""
        try:
            s = self.score
            return round(
                s.attendance * 0.2 + s.homework * 0.2 +
                s.quiz * 0.3 + s.exam * 0.3, 1
            )
        except Score.DoesNotExist:
            return 0.0

    def get_latest_prediction(self):
        """Eng oxirgi ML prognozni qaytaradi"""
        return self.predictions.order_by('-predicted_at').first()


class Score(models.Model):
    """
    O'quvchi umumiy natijalari — agregatsiya natijasi (0-100 foiz).
    Kunlik yozuvlar o'zgarsa recalculate_score() bu modelni avtomatik yangilaydi.
    """
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
        verbose_name="Quiz / Sinf ishi (%)"
    )
    exam       = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        verbose_name="Imtihon (%)"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table            = 'scores'
        verbose_name        = "Natija (umumiy)"
        verbose_name_plural = "Natijalar (umumiy)"

    def __str__(self):
        return (
            f"{self.student.name} → "
            f"att:{self.attendance} hw:{self.homework} q:{self.quiz} e:{self.exam}"
        )

    @property
    def weighted(self) -> float:
        """Weighted formula: att×0.2 + hw×0.2 + quiz×0.3 + exam×0.3"""
        return round(
            self.attendance * 0.2 + self.homework * 0.2 +
            self.quiz * 0.3 + self.exam * 0.3, 1
        )


# ═══════════════════════════════════════════════════════════════
#  KUNLIK MA'LUMOT MODELLARI
# ═══════════════════════════════════════════════════════════════

class DailyAttendance(models.Model):
    """
    Har bir dars uchun davomat yozuvi.

    Mantiq qoidalari:
        - is_present=True  → is_excused har doim False (clean() orqali majburlanadi)
        - is_present=False → is_excused True (sababli) yoki False (sababsiz) bo'lishi mumkin
    """
    student       = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name='attendances'
    )
    date          = models.DateField(verbose_name="Sana")
    lesson_number = models.PositiveSmallIntegerField(
        default=1, verbose_name="Dars raqami (1-chi, 2-chi...)"
    )
    is_present    = models.BooleanField(default=True, verbose_name="Keldi")
    is_excused    = models.BooleanField(
        default=False,
        verbose_name="Sababli (faqat kelmagan bo'lsa ahamiyatli)"
    )
    note          = models.CharField(max_length=255, blank=True, verbose_name="Izoh")
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table            = 'daily_attendances'
        verbose_name        = "Davomat yozuvi"
        verbose_name_plural = "Davomat yozuvlari"
        unique_together     = ['student', 'date', 'lesson_number']
        ordering            = ['-date', 'lesson_number']
        indexes             = [
            models.Index(fields=['student', '-date']),
        ]

    def clean(self):
        """
        Mantiq tekshiruvi:
        Kelgan o'quvchi "sababli kelmagan" bo'la olmaydi.
        """
        if self.is_present and self.is_excused:
            raise ValidationError(
                "Kelgan o'quvchini 'sababli kelmagan' deb belgilab bo'lmaydi."
            )

    def save(self, *args, **kwargs):
        # is_present=True bo'lsa is_excused ni avtomatik False ga o'zgartirish
        if self.is_present:
            self.is_excused = False
        super().save(*args, **kwargs)

    def __str__(self):
        if self.is_present:
            status = "✅ Keldi"
        elif self.is_excused:
            status = "📋 Sababli"
        else:
            status = "❌ Kelmadi"
        return f"{self.student.name} | {self.date} | {status}"


class HomeworkSubmission(models.Model):
    """
    Har bir uy vazifasi natijasi.

    Mantiq qoidalari:
        - submitted=False bo'lsa score avtomatik 0 ga tushadi
        - score > max_score bo'la olmaydi (clean() orqali tekshiriladi)
    """
    student   = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name='homeworks'
    )
    date      = models.DateField(verbose_name="Sana (topshirilgan)")
    title     = models.CharField(max_length=200, verbose_name="Uy vazifasi nomi / mavzusi")
    max_score = models.FloatField(
        default=10.0,
        verbose_name="Maksimal ball",
        validators=[MinValueValidator(0.1)]
    )
    score     = models.FloatField(
        default=0.0,
        verbose_name="Olingan ball",
        validators=[MinValueValidator(0.0)]
    )
    submitted  = models.BooleanField(default=True, verbose_name="Topshirildi")
    note       = models.CharField(max_length=255, blank=True, verbose_name="Izoh")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table            = 'homework_submissions'
        verbose_name        = "Uy vazifasi natijasi"
        verbose_name_plural = "Uy vazifalari natijalari"
        ordering            = ['-date']
        indexes             = [
            models.Index(fields=['student', '-date']),
        ]

    def clean(self):
        if self.score > self.max_score:
            raise ValidationError(
                f"Ball ({self.score}) maksimal balldan ({self.max_score}) oshib ketdi!"
            )

    def save(self, *args, **kwargs):
        # Topshirilmagan bo'lsa ball 0 bo'lishi shart
        if not self.submitted:
            self.score = 0.0
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.name} | {self.title} | {self.score}/{self.max_score}"

    @property
    def percentage(self) -> float:
        """Foizga aylantirish (0-100)"""
        if self.max_score and self.max_score > 0:
            return round(min(self.score / self.max_score * 100, 100.0), 1)
        return 0.0


class QuizResult(models.Model):
    """
    Quiz, sinf ishi va imtihon natijalari.

    quiz_type → Score maydoni:
        'quiz'      → Score.quiz  ga kiritiladi
        'classwork' → Score.quiz  ga kiritiladi
        'exam'      → Score.exam  ga kiritiladi
    """
    QUIZ_TYPE_CHOICES = [
        ('quiz',      'Quiz (kichik test)'),
        ('classwork', 'Sinf ishi'),
        ('exam',      'Imtihon'),
    ]

    student   = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name='quiz_results'
    )
    date      = models.DateField(verbose_name="Sana")
    quiz_type = models.CharField(
        max_length=20, choices=QUIZ_TYPE_CHOICES,
        default='quiz', verbose_name="Tur"
    )
    topic     = models.CharField(max_length=200, verbose_name="Mavzu")
    max_score = models.FloatField(
        default=100.0,
        verbose_name="Maksimal ball",
        validators=[MinValueValidator(0.1)]
    )
    score     = models.FloatField(
        default=0.0,
        verbose_name="Olingan ball",
        validators=[MinValueValidator(0.0)]
    )
    note       = models.CharField(max_length=255, blank=True, verbose_name="Izoh")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table            = 'quiz_results'
        verbose_name        = "Quiz / Imtihon natijasi"
        verbose_name_plural = "Quiz / Imtihon natijalari"
        ordering            = ['-date']
        indexes             = [
            models.Index(fields=['student', 'quiz_type', '-date']),
        ]

    def clean(self):
        if self.score > self.max_score:
            raise ValidationError(
                f"Ball ({self.score}) maksimal balldan ({self.max_score}) oshib ketdi!"
            )

    def __str__(self):
        type_label = dict(self.QUIZ_TYPE_CHOICES).get(self.quiz_type, self.quiz_type)
        return f"{self.student.name} | {type_label}: {self.score}/{self.max_score} | {self.date}"

    @property
    def percentage(self) -> float:
        """Foizga aylantirish (0-100)"""
        if self.max_score and self.max_score > 0:
            return round(min(self.score / self.max_score * 100, 100.0), 1)
        return 0.0


# ═══════════════════════════════════════════════════════════════
#  AVTOMATIK AGREGATSIYA — DB aggregation (N+1 yo'q)
# ═══════════════════════════════════════════════════════════════

def recalculate_score(student: 'Student') -> 'Score':
    """
    O'quvchining barcha kunlik yozuvlari asosida Score ni qayta hisoblash.
    DB aggregation ishlatiladi — Python loop yo'q, tezkor.

    Qoidalar:
        attendance = kelgan / jami × 100
        homework   = sum(score/max_score) / count × 100   (topshirilmagan → 0/max)
        quiz       = quiz + classwork turlari o'rtachasi (foizda)
        exam       = exam turi o'rtachasi (foizda)

    Agar biror tur bo'yicha yozuv yo'q → mavjud qiymat o'zgartirilmaydi.
    """
    score, _ = Score.objects.get_or_create(student=student)
    changed  = False

    # ── DAVOMAT ─────────────────────────────────────────────────
    att_agg = DailyAttendance.objects.filter(student=student).aggregate(
        total=Count('id'),
        present=Count('id', filter=Q(is_present=True))
    )
    if att_agg['total']:
        score.attendance = round(att_agg['present'] / att_agg['total'] * 100, 1)
        changed = True

    # ── UY VAZIFASI ──────────────────────────────────────────────
    # Har bir vazifa uchun (score/max_score) ni DB da hisoblash mumkin emas (division),
    # shuning uchun yengil Python loop ishlatamiz — lekin faqat 2 ta ustun olinadi
    hw_rows = HomeworkSubmission.objects.filter(
        student=student
    ).values_list('score', 'max_score')
    if hw_rows:
        valid = [(s, m) for s, m in hw_rows if m > 0]
        if valid:
            total_pct = sum(min(s / m, 1.0) for s, m in valid)
            score.homework = round(total_pct / len(valid) * 100, 1)
            changed = True

    # ── QUIZ / SINF ISHI ─────────────────────────────────────────
    quiz_rows = QuizResult.objects.filter(
        student=student, quiz_type__in=['quiz', 'classwork']
    ).values_list('score', 'max_score')
    if quiz_rows:
        valid = [(s, m) for s, m in quiz_rows if m > 0]
        if valid:
            total_pct = sum(min(s / m, 1.0) for s, m in valid)
            score.quiz = round(total_pct / len(valid) * 100, 1)
            changed = True

    # ── IMTIHON ──────────────────────────────────────────────────
    exam_rows = QuizResult.objects.filter(
        student=student, quiz_type='exam'
    ).values_list('score', 'max_score')
    if exam_rows:
        valid = [(s, m) for s, m in exam_rows if m > 0]
        if valid:
            total_pct = sum(min(s / m, 1.0) for s, m in valid)
            score.exam = round(total_pct / len(valid) * 100, 1)
            changed = True

    if changed:
        score.save()

    return score


def _calculate_trends(student: 'Student') -> dict:
    """
    Trend ko'rsatkichlarini hisoblash — ML model uchun qo'shimcha feature'lar.
    DB aggregation va minimal Python loop ishlatiladi.

    Returns:
        attendance_trend   : oxirgi hafta vs oldingi hafta davomat farqi (+/-)
        consecutive_absent : JORIY ketma-ket kelmaslik (max emas, joriy streak)
        hw_streak          : JORIY ketma-ket uy vazifasi topshirish
        quiz_improvement   : birinchi yarmga nisbatan ikkinchi yarmdagi quiz farqi
    """
    from django.utils import timezone
    from datetime import timedelta

    today        = timezone.now().date()
    one_week_ago = today - timedelta(days=7)

    # ── DAVOMAT TRENDI ───────────────────────────────────────────
    recent = DailyAttendance.objects.filter(
        student=student, date__gte=one_week_ago
    ).aggregate(total=Count('id'), present=Count('id', filter=Q(is_present=True)))

    older = DailyAttendance.objects.filter(
        student=student, date__lt=one_week_ago
    ).aggregate(total=Count('id'), present=Count('id', filter=Q(is_present=True)))

    attendance_trend = 0.0
    if recent['total'] and older['total']:
        recent_rate = recent['present'] / recent['total'] * 100
        older_rate  = older['present'] / older['total'] * 100
        attendance_trend = round(recent_rate - older_rate, 1)

    # ── JORIY KETMA-KET KELMASLIK (consecutive absent streak) ────
    # Oxirgi 30 kunni tekshiramiz
    recent_att = list(
        DailyAttendance.objects.filter(
            student=student,
            date__gte=today - timedelta(days=30)
        ).order_by('-date').values_list('is_present', flat=True)
    )
    consecutive_absent = 0
    for present in recent_att:
        if not present:
            consecutive_absent += 1
        else:
            break  # Birinchi kelgan kun — streak tugadi

    # ── JORIY UY VAZIFASI STREAK ─────────────────────────────────
    recent_hw = list(
        HomeworkSubmission.objects.filter(
            student=student,
            date__gte=today - timedelta(days=30)
        ).order_by('-date').values_list('submitted', flat=True)
    )
    hw_streak = 0
    for submitted in recent_hw:
        if submitted:
            hw_streak += 1
        else:
            break

    # ── QUIZ YAXSHILANISH TRENDI ─────────────────────────────────
    all_quiz_pcts = list(
        QuizResult.objects.filter(
            student=student, quiz_type__in=['quiz', 'classwork']
        ).order_by('date').values_list('score', 'max_score')
    )
    quiz_improvement = 0.0
    if len(all_quiz_pcts) >= 4:
        half       = len(all_quiz_pcts) // 2
        rest       = len(all_quiz_pcts) - half
        first_avg  = sum(
            (s / m * 100) for s, m in all_quiz_pcts[:half] if m > 0
        ) / half
        second_avg = sum(
            (s / m * 100) for s, m in all_quiz_pcts[half:] if m > 0
        ) / rest
        quiz_improvement = round(second_avg - first_avg, 1)

    return {
        'attendance_trend':   attendance_trend,
        'consecutive_absent': consecutive_absent,
        'hw_streak':          hw_streak,
        'quiz_improvement':   quiz_improvement,
    }


# ═══════════════════════════════════════════════════════════════
#  SIGNALS
# ═══════════════════════════════════════════════════════════════

@receiver(post_save, sender=Student)
def create_score_for_student(sender, instance, created, **kwargs):
    """Yangi o'quvchi qo'shilganda Score avtomatik yaratiladi"""
    if created:
        Score.objects.get_or_create(student=instance)


@receiver(post_save, sender=DailyAttendance)
def update_score_on_attendance(sender, instance, **kwargs):
    """Davomat yozilganda Score ni qayta hisoblash"""
    recalculate_score(instance.student)


@receiver(post_save, sender=HomeworkSubmission)
def update_score_on_homework(sender, instance, **kwargs):
    """Uy vazifasi kiritilganda Score ni qayta hisoblash"""
    recalculate_score(instance.student)


@receiver(post_save, sender=QuizResult)
def update_score_on_quiz(sender, instance, **kwargs):
    """Quiz/imtihon natijasi kiritilganda Score ni qayta hisoblash"""
    recalculate_score(instance.student)


@receiver(post_save, sender=Score)
def update_prediction_on_score(sender, instance, **kwargs):
    """
    Score o'zgarganda ML prognozni yaratish (create — tarix uchun).
    update_or_create emas, chunki har yangilanish tarixi saqlanishi kerak.
    Statistika viewlari '.order_by("-predicted_at").first()' bilan oxirgi prognozni oladi.
    """
    try:
        from ml.ml_service import get_prediction_with_trends
        from apps.predictions.models import Prediction

        trends          = _calculate_trends(instance.student)
        prediction_data = get_prediction_with_trends(
            attendance=instance.attendance,
            homework=instance.homework,
            quiz=instance.quiz,
            exam=instance.exam,
            **trends
        )

        Prediction.objects.create(
            student=instance.student,
            attendance=instance.attendance,
            homework=instance.homework,
            quiz=instance.quiz,
            exam=instance.exam,
            predicted_score=prediction_data['predicted_score'],
            level=prediction_data['level'],
            risk_percentage=prediction_data['risk_percentage'],
            recommendation=prediction_data['recommendation'],
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Prognoz yaratishda xato: {e}")
