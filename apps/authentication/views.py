from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .serializers import (
    LoginSerializer, TeacherSerializer,
    RegisterSerializer, ChangePasswordSerializer
)


class LoginView(APIView):
    """Username va parol orqali tizimga kirish — JWT token olish"""
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_id='auth_login',
        operation_summary='Tizimga kirish (username)',
        operation_description=(
            'Username va parol orqali JWT token olish.\n\n'
            '**Demo:** username: `teacher1` | parol: `Teacher123!`'
        ),
        tags=['🔐 Auth'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'password'],
            properties={
                'username': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    example='teacher1',
                    description='Foydalanuvchi nomi (kichik harflar)'
                ),
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    example='Teacher123!'
                ),
            }
        ),
        responses={
            200: openapi.Response('Muvaffaqiyatli kirish', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'token':   openapi.Schema(type=openapi.TYPE_STRING, description='Access token (24 soat)'),
                    'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token (7 kun)'),
                    'user':    openapi.Schema(type=openapi.TYPE_OBJECT),
                }
            )),
            401: "Noto'g'ri username yoki parol",
        }
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            data = serializer.validated_data
            return Response({
                'token':   data['token'],
                'refresh': data['refresh'],
                'user':    data['user'],
            }, status=status.HTTP_200_OK)

        return Response({
            'error': {'code': 401, 'message': serializer.errors}
        }, status=status.HTTP_401_UNAUTHORIZED)


class RegisterView(APIView):
    """Yangi o'qituvchi ro'yxatdan o'tishi"""
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_id='auth_register',
        operation_summary="Ro'yxatdan o'tish",
        tags=['🔐 Auth'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'name', 'email', 'password', 'password2'],
            properties={
                'username':  openapi.Schema(type=openapi.TYPE_STRING, example='ali_karimov'),
                'name':      openapi.Schema(type=openapi.TYPE_STRING, example='Abdulloh Karimov'),
                'email':     openapi.Schema(type=openapi.TYPE_STRING, example='ali@edu.uz'),
                'password':  openapi.Schema(type=openapi.TYPE_STRING, example='Parol123!'),
                'password2': openapi.Schema(type=openapi.TYPE_STRING, example='Parol123!'),
                'phone':     openapi.Schema(type=openapi.TYPE_STRING, example='+998901234567'),
                'subject':   openapi.Schema(type=openapi.TYPE_STRING, example='Matematika'),
            }
        ),
        responses={
            201: "Muvaffaqiyatli ro'yxatdan o'tish",
            400: "Xato ma'lumotlar"
        }
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            teacher = serializer.save()
            refresh = RefreshToken.for_user(teacher)
            return Response({
                'token':   str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id':       teacher.id,
                    'username': teacher.username,
                    'name':     teacher.name,
                    'email':    teacher.email,
                },
            }, status=status.HTTP_201_CREATED)

        return Response(
            {'error': {'code': 400, 'message': serializer.errors}},
            status=status.HTTP_400_BAD_REQUEST
        )


class LogoutView(APIView):
    """Tizimdan chiqish — tokenni blacklist ga qo'shish"""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_id='auth_logout',
        operation_summary='Tizimdan chiqish',
        tags=['🔐 Auth'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['refresh'],
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token')
            }
        ),
        responses={200: 'Muvaffaqiyatli chiqildi', 400: "Token noto'g'ri"}
    )
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'error': 'refresh token majburiy'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Muvaffaqiyatli chiqildi'})
        except TokenError:
            return Response(
                {'error': "Token noto'g'ri yoki muddati tugagan"},
                status=status.HTTP_400_BAD_REQUEST
            )


class ProfileView(APIView):
    """Joriy foydalanuvchi profili"""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_id='auth_me_get',
        operation_summary="Profilni ko'rish",
        tags=['🔐 Auth'],
        responses={200: TeacherSerializer}
    )
    def get(self, request):
        return Response(TeacherSerializer(request.user).data)

    @swagger_auto_schema(
        operation_id='auth_me_update',
        operation_summary='Profilni yangilash',
        tags=['🔐 Auth'],
        request_body=TeacherSerializer,
        responses={200: TeacherSerializer}
    )
    def put(self, request):
        serializer = TeacherSerializer(
            request.user, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(
            {'error': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )


class ChangePasswordView(APIView):
    """Parol o'zgartirish"""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_id='auth_change_password',
        operation_summary="Parol o'zgartirish",
        tags=['🔐 Auth'],
        request_body=ChangePasswordSerializer,
        responses={200: "Parol muvaffaqiyatli o'zgartirildi", 400: "Xato"}
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'error': "Eski parol noto'g'ri"},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"message": "Parol muvaffaqiyatli o'zgartirildi. Qayta kiring."})
