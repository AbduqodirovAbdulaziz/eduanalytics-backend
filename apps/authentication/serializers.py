from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import Teacher
import re


class LoginSerializer(serializers.Serializer):
    """Username va parol orqali tizimga kirish"""
    username = serializers.CharField(max_length=50)
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get('username', '').lower().strip()
        password = data.get('password')

        user = authenticate(
            request=self.context.get('request'),
            username=username,
            password=password
        )

        if not user:
            raise serializers.ValidationError(
                {"message": "Username yoki parol noto'g'ri"}
            )
        if not user.is_active:
            raise serializers.ValidationError(
                {"message": "Hisob bloklangan. Admin bilan bog'laning."}
            )

        refresh = RefreshToken.for_user(user)
        return {
            'token':   str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id':       user.id,
                'username': user.username,
                'name':     user.name,
                'email':    user.email,
                'subject':  user.subject,
            }
        }


class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Teacher
        fields = ['id', 'username', 'name', 'email', 'phone', 'subject', 'created_at']
        read_only_fields = ['id', 'created_at']


class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model  = Teacher
        fields = ['username', 'name', 'email', 'password', 'password2', 'phone', 'subject']

    def validate_username(self, value):
        value = value.lower().strip()
        if not re.match(r'^[a-z0-9_]+$', value):
            raise serializers.ValidationError(
                "Username faqat kichik harflar, raqamlar va _ dan iborat bo'lishi kerak"
            )
        if Teacher.objects.filter(username=value).exists():
            raise serializers.ValidationError("Bu username allaqachon band")
        return value

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Parollar mos kelmaydi"})

        password = data['password']
        errors = []
        if not re.search(r'[A-Z]', password):
            errors.append("Hech bo'lmaganda 1 ta KATTA harf bo'lishi kerak")
        if not re.search(r'[a-z]', password):
            errors.append("Hech bo'lmaganda 1 ta kichik harf bo'lishi kerak")
        if not re.search(r'[0-9]', password):
            errors.append("Hech bo'lmaganda 1 ta raqam bo'lishi kerak")
        if not re.search(r'[@$!%*#?&]', password):
            errors.append("Hech bo'lmaganda 1 ta maxsus belgi (@$!%*#?&) bo'lishi kerak")
        if errors:
            raise serializers.ValidationError({"password": errors})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        teacher  = Teacher(**validated_data)
        teacher.set_password(password)
        teacher.save()
        return teacher


class ChangePasswordSerializer(serializers.Serializer):
    """Parol o'zgartirish"""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value):
        errors = []
        if not re.search(r'[A-Z]', value):
            errors.append("Hech bo'lmaganda 1 ta KATTA harf bo'lishi kerak")
        if not re.search(r'[0-9]', value):
            errors.append("Hech bo'lmaganda 1 ta raqam bo'lishi kerak")
        if errors:
            raise serializers.ValidationError(errors)
        return value
