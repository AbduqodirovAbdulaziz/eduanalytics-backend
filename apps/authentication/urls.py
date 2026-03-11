from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import LoginView, RegisterView, LogoutView, ProfileView, ChangePasswordView

urlpatterns = [
    path('login',           LoginView.as_view(),         name='auth-login'),
    path('register',        RegisterView.as_view(),       name='auth-register'),
    path('logout',          LogoutView.as_view(),         name='auth-logout'),
    path('me',              ProfileView.as_view(),        name='auth-me'),
    path('change-password', ChangePasswordView.as_view(), name='auth-change-password'),
    path('refresh',         TokenRefreshView.as_view(),   name='token-refresh'),
]
