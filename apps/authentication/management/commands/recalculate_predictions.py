"""
Barcha eski prognozlarni o'chirib, yangi AQLLI recommendation bilan qayta hisoblash.

Ishlatish:
    python manage.py recalculate_predictions
    python manage.py recalculate_predictions --dry-run   (faqat ko'rish, o'zgartirmaslik)
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.students.models import Student, Score
from apps.predictions.models import Prediction
from ml.ml_service import get_prediction


class Command(BaseCommand):
    help = "Barcha prognozlarni o'chirib, yangi recommendation bilan qayta hisoblash"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help="Faqat natijani ko'rish, bazaga yozmaydi",
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING("⚠️  DRY-RUN rejimi — bazaga yozilmaydi\n"))

        # ── 1. Statistika ──────────────────────────────────────────
        total_predictions = Prediction.objects.count()
        total_students    = Student.objects.count()
        students_with_score = Student.objects.filter(score__isnull=False).count()

        self.stdout.write("=" * 60)
        self.stdout.write("📊 JORIY HOLAT:")
        self.stdout.write(f"   Jami o'quvchilar     : {total_students}")
        self.stdout.write(f"   Natijasi bor         : {students_with_score}")
        self.stdout.write(f"   Eski prognozlar soni : {total_predictions}")
        self.stdout.write("=" * 60)

        if total_students == 0:
            self.stdout.write(self.style.WARNING(
                "\n⚠️  Bazada o'quvchi yo'q. Avval demo ma'lumot yuklang:\n"
                "   python manage.py seed_data\n"
            ))
            return

        # ── 2. Eski prognozlarni o'chirish ─────────────────────────
        if not dry_run:
            self.stdout.write("\n🗑️  Eski prognozlar o'chirilmoqda...")
            deleted_count, _ = Prediction.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(
                f"   ✅ {deleted_count} ta eski prognoz o'chirildi"
            ))
        else:
            self.stdout.write(f"\n[DRY-RUN] {total_predictions} ta prognoz o'chirilishi kerak edi")

        # ── 3. Qayta hisoblash ─────────────────────────────────────
        self.stdout.write("\n🤖 Yangi prognozlar hisoblanmoqda...\n")

        success_count = 0
        skip_count    = 0
        error_count   = 0

        students = Student.objects.select_related('score').all()

        for student in students:
            try:
                score = student.score
            except Score.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f"   ⏭  {student.name} — score yo'q, o'tkazib yuborildi")
                )
                skip_count += 1
                continue

            try:
                # Yangi aqlli recommendation bilan prognoz
                result = get_prediction(
                    attendance=score.attendance,
                    homework=score.homework,
                    quiz=score.quiz,
                    exam=score.exam,
                )

                if not dry_run:
                    with transaction.atomic():
                        Prediction.objects.create(
                            student=student,
                            attendance=score.attendance,
                            homework=score.homework,
                            quiz=score.quiz,
                            exam=score.exam,
                            predicted_score=result['predicted_score'],
                            level=result['level'],
                            risk_percentage=result['risk_percentage'],
                            recommendation=result['recommendation'],
                        )

                # Ko'rish uchun qisqa chiqish
                level_icon = {
                    'High Performance':   '🟢',
                    'Medium Performance': '🟡',
                    'Low Performance':    '🔴',
                }.get(result['level'], '⚪')

                self.stdout.write(
                    f"   {level_icon} {student.name:<25} "
                    f"ball={result['predicted_score']:.1f} | "
                    f"xavf={result['risk_percentage']:.1f}% | "
                    f"{result['level']}"
                )
                success_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"   ❌ {student.name} — xato: {e}")
                )
                error_count += 1

        # ── 4. Yakuniy hisobot ─────────────────────────────────────
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("📋 YAKUNIY HISOBOT:")
        self.stdout.write(self.style.SUCCESS(f"   ✅ Muvaffaqiyatli : {success_count} ta"))
        if skip_count:
            self.stdout.write(self.style.WARNING(f"   ⏭  O'tkazildi    : {skip_count} ta (score yo'q)"))
        if error_count:
            self.stdout.write(self.style.ERROR(f"   ❌ Xato           : {error_count} ta"))

        # Daraja taqsimoti
        if not dry_run and success_count > 0:
            high   = Prediction.objects.filter(level='High Performance').count()
            medium = Prediction.objects.filter(level='Medium Performance').count()
            low    = Prediction.objects.filter(level='Low Performance').count()

            self.stdout.write("\n📊 DARAJA TAQSIMOTI:")
            self.stdout.write(f"   🟢 High Performance   : {high} ta")
            self.stdout.write(f"   🟡 Medium Performance : {medium} ta")
            self.stdout.write(f"   🔴 Low Performance    : {low} ta")

        self.stdout.write("=" * 60)

        if dry_run:
            self.stdout.write(self.style.WARNING(
                "\n⚠️  DRY-RUN — hech narsa o'zgarmadi.\n"
                "   Haqiqiy bajarish uchun:\n"
                "   python manage.py recalculate_predictions\n"
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"\n🎉 Barcha {success_count} ta prognoz yangi recommendation bilan qayta hisoblandi!\n"
            ))
