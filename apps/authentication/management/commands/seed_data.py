"""
Demo ma'lumotlar yaratish skripti
Ishlatish: python manage.py seed_data
"""
import random
from django.core.management.base import BaseCommand
from apps.authentication.models import Teacher
from apps.courses.models import Course
from apps.groups.models import Group
from apps.students.models import Student, Score


FIRST_NAMES = ["Alibek", "Jasur", "Dilnoza", "Malika", "Bobur", "Sarvar",
               "Gulnora", "Aziz", "Kamola", "Sherzod", "Nilufar", "Davron",
               "Madina", "Ulugbek", "Zulfiya"]
LAST_NAMES  = ["Karimov", "Toshmatov", "Yusupov", "Rahimov", "Nazarov",
               "Xolmatov", "Mirzayev", "Abdullayev", "Ismoilov", "Qalandarov"]

COURSES = [
    ("Matematika",  "math"),
    ("Fizika",      "physics"),
    ("Ingliz tili", "english"),
    ("Informatika", "it"),
]

GROUPS = ["A-guruh", "B-guruh", "C-guruh"]


class Command(BaseCommand):
    help = "Demo ma'lumotlarni bazaga yuklash"

    def handle(self, *args, **kwargs):
        self.stdout.write("📦 Demo ma'lumotlar yaratilmoqda...\n")

        # ✅ Username bilan teacher yaratish
        teacher, created = Teacher.objects.get_or_create(
            username='teacher1',
            defaults={
                'name':     'Abdulloh Karimov',
                'email':    'teacher@edu.uz',
                'subject':  'Matematika',
                'is_staff': True,
            }
        )
        if created:
            teacher.set_password('Teacher123!')
            teacher.save()
            self.stdout.write("  ✅ O'qituvchi yaratildi:")
        else:
            self.stdout.write("  ℹ️  O'qituvchi allaqachon mavjud:")

        self.stdout.write(f"     Username : teacher1")
        self.stdout.write(f"     Parol    : Teacher123!")
        self.stdout.write(f"     Email    : teacher@edu.uz\n")
        self.stdout.write("  ⚠️  Superuser yaratish:")
        self.stdout.write("     python manage.py createsuperuser\n")

        # Courses + Groups + Students
        total_students = 0
        for course_name, subject in COURSES:
            course, _ = Course.objects.get_or_create(
                name=course_name, teacher=teacher,
                defaults={'subject': subject, 'description': f'{course_name} kursi'}
            )
            for group_name in GROUPS:
                group, _ = Group.objects.get_or_create(name=group_name, course=course)

                for _ in range(random.randint(5, 8)):
                    fname   = random.choice(FIRST_NAMES)
                    lname   = random.choice(LAST_NAMES)
                    student = Student.objects.create(
                        name=f"{fname} {lname}",
                        email=f"{fname.lower()}.{lname.lower()}{random.randint(1,99)}@mail.uz",
                        group=group,
                    )
                    # Signal orqali Score yaratiladi, uni yangilaymiz
                    score = student.score
                    score.attendance = round(random.uniform(30, 100), 1)
                    score.homework   = round(random.uniform(20, 100), 1)
                    score.quiz       = round(random.uniform(15, 100), 1)
                    score.exam       = round(random.uniform(10, 100), 1)
                    score.save()
                    total_students += 1

        self.stdout.write(f"  ✅ {total_students} ta o'quvchi yaratildi")
        self.stdout.write(self.style.SUCCESS(
            "\n🎉 Demo ma'lumotlar muvaffaqiyatli yuklandi!\n"
            "   Login: username=teacher1 | parol=Teacher123!"
        ))
