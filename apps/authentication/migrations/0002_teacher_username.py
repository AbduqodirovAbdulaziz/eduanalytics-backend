"""
Migration: Teacher modeliga username field qo'shish
Email o'rniga username bilan login qilish uchun
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),
    ]

    operations = [
        # 1. username field qo'shish (vaqtinchalik blank=True)
        migrations.AddField(
            model_name='teacher',
            name='username',
            field=models.CharField(
                max_length=50,
                unique=False,
                blank=True,
                default='',
                verbose_name='Foydalanuvchi nomi',
                help_text='Faqat kichik harflar, raqamlar va _ belgisi'
            ),
        ),

        # 2. Mavjud foydalanuvchilar uchun email dan username generatsiya qilish
        migrations.RunSQL(
            sql="""
                UPDATE teachers
                SET username = LOWER(REPLACE(SUBSTR(email, 1,
                    CASE WHEN INSTR(email, '@') > 0
                         THEN INSTR(email, '@') - 1
                         ELSE LENGTH(email) END
                ), '.', '_'))
                WHERE username = '' OR username IS NULL;
            """,
            reverse_sql="UPDATE teachers SET username = '' WHERE username IS NOT NULL;"
        ),

        # 3. unique=True, blank=False qilish
        migrations.AlterField(
            model_name='teacher',
            name='username',
            field=models.CharField(
                max_length=50,
                unique=True,
                verbose_name='Foydalanuvchi nomi',
                help_text='Faqat kichik harflar, raqamlar va _ belgisi (masalan: ali_karimov)'
            ),
        ),
    ]
