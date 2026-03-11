from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Teacher


@admin.register(Teacher)
class TeacherAdmin(UserAdmin):
    list_display       = ['username', 'name', 'email', 'subject', 'is_active', 'is_staff', 'created_at']
    list_display_links = ['username', 'name']
    list_filter        = ['is_active', 'is_staff', 'subject']
    search_fields      = ['username', 'name', 'email']
    ordering           = ['-created_at']
    list_per_page      = 25

    fieldsets = (
        ("🔑 Kirish ma'lumotlari", {
            'fields': ('username', 'email', 'password')
        }),
        ("👤 Shaxsiy ma'lumot", {
            'fields': ('name', 'phone', 'subject')
        }),
        ('🔐 Ruxsatlar', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',),
        }),
        ('📅 Sanalar', {
            'fields': ('last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    add_fieldsets = (
        ("🔑 Login ma'lumotlari", {
            'classes': ('wide',),
            'fields': ('username', 'email', 'name', 'password1', 'password2'),
        }),
        ('📋 Qo\'shimcha', {
            'classes': ('wide',),
            'fields': ('phone', 'subject', 'is_staff'),
        }),
    )

    readonly_fields = ['last_login', 'created_at', 'updated_at']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(id=request.user.id)
        return qs

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser
