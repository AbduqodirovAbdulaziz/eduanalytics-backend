"""
Migration: 0002 — DailyAttendance, HomeworkSubmission, QuizResult modellari qo'shildi
"""
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0001_initial'),
    ]

    operations = [

        # ── DailyAttendance ──────────────────────────────────────────
        migrations.CreateModel(
            name='DailyAttendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='Sana')),
                ('lesson_number', models.PositiveSmallIntegerField(default=1, verbose_name='Dars raqami (1-chi, 2-chi...)')),
                ('is_present', models.BooleanField(default=True, verbose_name='Keldi')),
                ('is_excused', models.BooleanField(default=False, verbose_name='Sababli (agar kelmagan bo\'lsa)')),
                ('note', models.CharField(blank=True, max_length=255, verbose_name='Izoh')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendances', to='students.student')),
            ],
            options={
                'verbose_name': 'Davomat yozuvi',
                'verbose_name_plural': 'Davomat yozuvlari',
                'db_table': 'daily_attendances',
                'ordering': ['-date', 'lesson_number'],
            },
        ),

        migrations.AddIndex(
            model_name='dailyattendance',
            index=models.Index(fields=['student', '-date'], name='daily_att_student_date_idx'),
        ),

        migrations.AlterUniqueTogether(
            name='dailyattendance',
            unique_together={('student', 'date', 'lesson_number')},
        ),

        # ── HomeworkSubmission ───────────────────────────────────────
        migrations.CreateModel(
            name='HomeworkSubmission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='Sana (topshirilgan)')),
                ('title', models.CharField(max_length=200, verbose_name='Uy vazifasi nomi / mavzusi')),
                ('max_score', models.FloatField(default=10.0, verbose_name='Maksimal ball', validators=[django.core.validators.MinValueValidator(0.1)])),
                ('score', models.FloatField(default=0.0, verbose_name='Olingan ball', validators=[django.core.validators.MinValueValidator(0.0)])),
                ('submitted', models.BooleanField(default=True, verbose_name='Topshirildi')),
                ('note', models.CharField(blank=True, max_length=255, verbose_name='Izoh')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='homeworks', to='students.student')),
            ],
            options={
                'verbose_name': 'Uy vazifasi natijasi',
                'verbose_name_plural': 'Uy vazifalari natijalari',
                'db_table': 'homework_submissions',
                'ordering': ['-date'],
            },
        ),

        migrations.AddIndex(
            model_name='homeworksubmission',
            index=models.Index(fields=['student', '-date'], name='homework_student_date_idx'),
        ),

        # ── QuizResult ───────────────────────────────────────────────
        migrations.CreateModel(
            name='QuizResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='Sana')),
                ('quiz_type', models.CharField(
                    choices=[('quiz', 'Quiz (kichik test)'), ('classwork', 'Sinf ishi'), ('exam', 'Imtihon')],
                    default='quiz', max_length=20, verbose_name='Tur'
                )),
                ('topic', models.CharField(max_length=200, verbose_name='Mavzu')),
                ('max_score', models.FloatField(default=100.0, verbose_name='Maksimal ball', validators=[django.core.validators.MinValueValidator(0.1)])),
                ('score', models.FloatField(default=0.0, verbose_name='Olingan ball', validators=[django.core.validators.MinValueValidator(0.0)])),
                ('note', models.CharField(blank=True, max_length=255, verbose_name='Izoh')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quiz_results', to='students.student')),
            ],
            options={
                'verbose_name': 'Quiz / Imtihon natijasi',
                'verbose_name_plural': 'Quiz / Imtihon natijalari',
                'db_table': 'quiz_results',
                'ordering': ['-date'],
            },
        ),

        migrations.AddIndex(
            model_name='quizresult',
            index=models.Index(fields=['student', 'quiz_type', '-date'], name='quiz_student_type_date_idx'),
        ),

        # ── Score verbose_name yangilash ─────────────────────────────
        migrations.AlterField(
            model_name='score',
            name='quiz',
            field=models.FloatField(
                default=0.0,
                validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(100.0)],
                verbose_name='Quiz / Sinf ishi (%)'
            ),
        ),
    ]
