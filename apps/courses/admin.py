from django.contrib import admin
from .models import Course


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display  = ['name', 'subject', 'teacher', 'group_count', 'student_count', 'created_at']
    list_filter   = ['subject']
    search_fields = ['name', 'teacher__name']

    def get_queryset(self, request):
        """O'qituvchilar faqat o'z kurslarini ko'rsin"""
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(teacher=request.user)
        return qs

    def has_add_permission(self, request):
        """Faqat o'qituvchilar kurs qo'sha olsin"""
        return request.user.is_staff or request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        """O'qituvchilar faqat o'z kurslarini o'chira olsin"""
        if not request.user.is_superuser and obj:
            return obj.teacher == request.user
        return request.user.is_superuser

    def save_model(self, request, obj, form, change):
        """Yangi kurs qo'shganda o'qituvchi avtomatik tayinlansin"""
        if not change:
            obj.teacher = request.user
        super().save_model(request, obj, form, change)
