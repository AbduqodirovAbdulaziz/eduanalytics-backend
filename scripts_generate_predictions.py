"""
Barcha o'quvchilar uchun avtomatik prognozlarni yaratish
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.students.models import Student, Score
from apps.predictions.models import Prediction
from ml.ml_service import calculate_prediction

# Barcha predictions o'chirish
Prediction.objects.all().delete()
print("✅ Eski prognozlar o'chirildi")

# Barcha o'quvchilar uchun prognozlarni yaratish
count = 0
for score in Score.objects.all():
    pred_data = calculate_prediction(
        attendance=score.attendance,
        homework=score.homework,
        quiz=score.quiz,
        exam=score.exam
    )
    Prediction.objects.update_or_create(
        student=score.student,
        defaults={
            'attendance': score.attendance,
            'homework': score.homework,
            'quiz': score.quiz,
            'exam': score.exam,
            'predicted_score': pred_data['predicted_score'],
            'level': pred_data['level'],
            'risk_percentage': pred_data['risk_percentage'],
            'recommendation': pred_data['recommendation'],
        }
    )
    count += 1

print(f"✅ {count} ta prognoz yaratildi!")
print("\n📊 Prognoz Statistikasi:")
print(f"  - High Performance: {Prediction.objects.filter(level='High Performance').count()}")
print(f"  - Medium Performance: {Prediction.objects.filter(level='Medium Performance').count()}")
print(f"  - Low Performance: {Prediction.objects.filter(level='Low Performance').count()}")
