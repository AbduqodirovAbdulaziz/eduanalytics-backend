from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class TeacherManager(BaseUserManager):
    def create_user(self, username, email, name, password=None, **extra_fields):
        if not username:
            raise ValueError("Username majburiy!")
        if not email:
            raise ValueError("Email majburiy!")
        email    = self.normalize_email(email)
        username = username.lower().strip()
        user     = self.model(username=username, email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, name, password, **extra_fields)


class Teacher(AbstractBaseUser, PermissionsMixin):
    """O'qituvchi modeli — tizimning asosiy foydalanuvchisi"""
    username   = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Foydalanuvchi nomi",
        help_text="Faqat kichik harflar, raqamlar va _ belgisi (masalan: ali_karimov)"
    )
    name       = models.CharField(max_length=150, verbose_name="Ism Familiya")
    email      = models.EmailField(unique=True, verbose_name="Email")
    phone      = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefon")
    subject    = models.CharField(max_length=100, blank=True, null=True, verbose_name="Fan")
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ✅ LOGIN username orqali amalga oshiriladi
    USERNAME_FIELD  = 'username'
    REQUIRED_FIELDS = ['email', 'name']

    objects = TeacherManager()

    class Meta:
        db_table            = 'teachers'
        verbose_name        = "O'qituvchi"
        verbose_name_plural = "O'qituvchilar"

    def __str__(self):
        return f"{self.name} (@{self.username})"
